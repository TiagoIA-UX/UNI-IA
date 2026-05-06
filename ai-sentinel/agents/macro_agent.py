from typing import Optional

import yfinance as yf
from agents.market_utils import resolve_market_ticker
from core.feature_store import FeatureStore
from core.schemas import AgentSignal
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object

class MacroAgent:
    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.llm = GroqClient()
        self.feature_store = feature_store or FeatureStore()
        self.system_prompt = """
        Você é o MacroAgent. Avalie os DADOS REAIS DE MERCADO E COTAÇÃO.
        Identifique o ambiente Risk-On (Apetite a risco) ou Risk-Off (Aversão a risco) do ativo.
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "signal_type": "RISK-ON" ou "RISK-OFF" ou "NEUTRAL",
            "confidence": 75.0,
            "summary": "Análise focada em performance percentual de longo e curto prazo e aversão ao risco."
        }
        """
        
    def _get_ticker(self, asset: str) -> str:
        return resolve_market_ticker(asset)

    def fetch_real_market_data(self, asset: str) -> dict:
        ticker_str = self._get_ticker(asset)
        ticker = yf.Ticker(ticker_str)
        
        info = ticker.info # Buscar real infos
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info and 'previousClose' not in info:
             # Tento baixar histórico para extrair o dado de fechamento (para casos que info fica vazio em moedas via yf)
             hist = ticker.history(period="5d")
             if hist.empty:
                  raise ValueError(f"Não há dados recentes de mercado reais em bolsa para o ativo {asset} ({ticker_str}) via YFinance.")
             info = {
                 "currentPrice": hist["Close"].iloc[-1],
                 "previousClose": hist["Close"].iloc[-2],
                 "volume": hist["Volume"].iloc[-1]
             }

        price = info.get("currentPrice") or info.get("regularMarketPrice") or getattr(ticker.fast_info, 'last_price', None)
        prev_close = info.get("previousClose") or getattr(ticker.fast_info, 'previous_close', None)
        
        if not price or not prev_close:
             raise ValueError(f"Dados de preço incompletos para {asset} no provedor de mercado YFinance.")
             
        variation = ((price - prev_close) / prev_close) * 100
        
        recent_volume = info.get("volume")
        return {
            "asset": asset,
            "ticker": ticker_str,
            "current_price": float(price),
            "previous_close": float(prev_close),
            "daily_variation_pct": round(float(variation), 6),
            "recent_volume": float(recent_volume) if recent_volume not in (None, "Desconhecido") else None,
        }

    def _format_market_data(self, payload: dict) -> str:
        market_stats = f"Ativo: {payload['asset']} (Ticker: {payload['ticker']})\n"
        market_stats += f"Preço Atual (Real-time): {payload['current_price']}\n"
        market_stats += f"Fechamento Anterior: {payload['previous_close']}\n"
        market_stats += f"Variação Diária: {payload['daily_variation_pct']:.2f}%\n"
        market_stats += f"Volume Recente: {payload.get('recent_volume', 'Desconhecido')}\n"
        return market_stats

    def analyze_macro_context(self, asset: str, signal_id: Optional[str] = None) -> AgentSignal:
        market_features = self.fetch_real_market_data(asset)
        real_data = self._format_market_data(market_features)
        
        prompt = f"Avalie a variação percentual de mercado HOJE (Agors) para o ativo {asset} com base nos dados brutos reais de tela:\n{real_data}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        data = extract_json_object(response)

        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="MacroAgent",
                features={
                    **market_features,
                    "emitted_confidence": float(data["confidence"]),
                },
                metadata={
                    "signal_type": data["signal_type"],
                    "summary": data["summary"],
                },
            )
        
        return AgentSignal(
            agent_name="MacroAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=real_data
        )
