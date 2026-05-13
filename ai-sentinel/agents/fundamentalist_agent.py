from typing import Optional

import yfinance as yf
from agents.market_utils import resolve_market_ticker
from core.feature_store import FeatureStore
from core.schemas import AgentSignal, LlmProvenance
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object

class FundamentalistAgent:
    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.llm = GroqClient()
        self.feature_store = feature_store or FeatureStore()
        self.system_prompt = """
        Você é o FundamentalistAgent. Sua missão é proteger o capital analisando os fundamentos, balanços e saúde financeira.
        Identifique distorções de preço em relação ao valor intrínseco (P/L, ROE, VPA).
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "signal_type": "UNDERVALUED" ou "OVERVALUED" ou "FAIR",
            "confidence": 90.0,
            "summary": "Resumo dos múltiplos fundamentalistas e solidez estrutural."
        }
        """

    def fetch_fundamentals(self, asset: str) -> dict:
        # Moedas não têm fundamentos tradicionais de ações, então filtramos
        asset_upper = asset.upper().strip()
        if asset_upper in ["USD", "EUR"] or asset_upper.endswith("USDT") or (len(asset_upper) == 6 and asset_upper.isalpha()):
            raw_text = f"Ativo cambial ({asset}). A análise fundamentalista dele se baseia na balança comercial e diferencial de juros (já coberto pelo MacroAgent)."
            return {
                "asset": asset,
                "is_fx_like": True,
                "trailing_pe": None,
                "price_to_book": None,
                "return_on_equity": None,
                "profit_margins": None,
                "raw_text": raw_text,
            }

        ticker_str = resolve_market_ticker(asset_upper)
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        
        if not info or 'forwardPE' not in info:
            raw_text = f"Dados fundamentalistas estruturados indisponíveis ou não aplicáveis ao ativo {asset} no momento."
            return {
                "asset": asset,
                "is_fx_like": False,
                "trailing_pe": None,
                "price_to_book": None,
                "return_on_equity": None,
                "profit_margins": None,
                "raw_text": raw_text,
            }

        payload = {
            "asset": asset,
            "is_fx_like": False,
            "trailing_pe": info.get("trailingPE"),
            "price_to_book": info.get("priceToBook"),
            "return_on_equity": info.get("returnOnEquity"),
            "profit_margins": info.get("profitMargins"),
        }
        fund_data = f"Ativo: {asset}\n"
        fund_data += f"P/L (Preço/Lucro): {payload['trailing_pe']}\n"
        fund_data += f"P/VP (Preço/Valor Patrimonial): {payload['price_to_book']}\n"
        fund_data += f"ROE: {payload['return_on_equity']}\n"
        fund_data += f"Margem Líquida: {payload['profit_margins']}\n"
        payload["raw_text"] = fund_data
        return payload

    def analyze_fundamentals(self, asset: str, signal_id: Optional[str] = None, strategy_legenda: Optional[str] = None) -> AgentSignal:
        fundamentals = self.fetch_fundamentals(asset)
        fund_data = fundamentals["raw_text"]
        prompt = f"Atue bloqueando riscos. Analise estes fundamentos corporativos:\n{fund_data}"
        if strategy_legenda:
            prompt = f"[Contexto por timeframe]\n{strategy_legenda}\n\n{prompt}"
        
        comp = self.llm.complete(self.system_prompt, prompt)

        data = extract_json_object(comp.text)

        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="FundamentalistAgent",
                features={
                    "is_fx_like": fundamentals["is_fx_like"],
                    "trailing_pe": fundamentals["trailing_pe"],
                    "price_to_book": fundamentals["price_to_book"],
                    "return_on_equity": fundamentals["return_on_equity"],
                    "profit_margins": fundamentals["profit_margins"],
                    "emitted_confidence": float(data["confidence"]),
                },
                metadata={
                    "signal_type": data["signal_type"],
                    "summary": data["summary"],
                },
            )
        
        return AgentSignal(
            agent_name="FundamentalistAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=fund_data,
            llm_provenance=LlmProvenance(
                provider=comp.provider,
                model=comp.model,
                status="llm_success",
                detail="fundamentals",
            ),
        )