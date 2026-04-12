import json
import re
import yfinance as yf
from ..core.schemas import AgentSignal
from ..llm.groq_client import GroqClient

class FundamentalistAgent:
    def __init__(self):
        self.llm = GroqClient()
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

    def fetch_fundamentals(self, asset: str) -> str:
        # Moedas não têm fundamentos tradicionais de ações, então filtramos
        asset_upper = asset.upper().strip()
        if asset_upper in ["USD", "EUR"]:
            return f"Ativo cambial ({asset}). A análise fundamentalista dele se baseia na balança comercial e diferencial de juros (já coberto pelo MacroAgent)."
            
        ticker_str = f"{asset_upper}.SA" if not asset_upper.endswith(".SA") and not asset_upper.startswith("^") else asset_upper
        ticker = yf.Ticker(ticker_str)
        info = ticker.info
        
        if not info or 'forwardPE' not in info:
            return f"Dados fundamentalistas estruturados indisponíveis ou não aplicáveis ao ativo {asset} no momento."

        fund_data = f"Ativo: {asset}\n"
        fund_data += f"P/L (Preço/Lucro): {info.get('trailingPE', 'N/A')}\n"
        fund_data += f"P/VP (Preço/Valor Patrimonial): {info.get('priceToBook', 'N/A')}\n"
        fund_data += f"ROE: {info.get('returnOnEquity', 'N/A')}\n"
        fund_data += f"Margem Líquida: {info.get('profitMargins', 'N/A')}\n"
        
        return fund_data

    def analyze_fundamentals(self, asset: str) -> AgentSignal:
        fund_data = self.fetch_fundamentals(asset)
        prompt = f"Atue bloqueando riscos. Analise estes fundamentos corporativos:\n{fund_data}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Groq falhou no FundamentalistAgent. Raw: {response}")
            
        data = json.loads(json_match.group(0))
        
        return AgentSignal(
            agent_name="FundamentalistAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=fund_data
        )