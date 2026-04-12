import json
import re
import yfinance as yf
from ..core.schemas import AgentSignal
from ..llm.groq_client import GroqClient

class TrendsAgent:
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = """
        Você é o TrendsAgent. Analise os picos de interesse do público e do mercado pelo ativo baseado em discrepância de Volume Transacionado Hoje x Média dos últimos 10 dias.
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "signal_type": "FOMO" ou "FEAR" ou "IGNORE",
            "confidence": 88.0,
            "summary": "Análise técnica justificando o FOMO ou Desinteresse do ativo pelas disparidades de volume nas negociações."
        }
        """
        
    def _get_ticker(self, asset: str) -> str:
        asset = asset.upper().strip()
        if asset == "USD": return "USDBRL=X"
        if asset == "EUR": return "EURBRL=X"
        if asset == "BRL": return "^BVSP" # IBOVESPA 
        if not asset.endswith(".SA") and not asset.endswith("=X") and not asset.startswith("^"):
            return f"{asset}.SA"
        return asset

    def fetch_real_volume_data(self, asset: str) -> str:
        ticker_str = self._get_ticker(asset)
        ticker = yf.Ticker(ticker_str)
        hist = ticker.history(period="15d")
        
        if hist.empty or 'Volume' not in hist.columns:
            raise ValueError(f"Não há dados recentes de volume de Ticker para Trends no YFinance ({ticker_str}) para o ativo {asset}")
            
        recent_vol = hist["Volume"].iloc[-1]
        historical_avg_vol = hist["Volume"].iloc[-10:-1].mean() if len(hist) > 10 else recent_vol
        
        if historical_avg_vol <= 0:
            vol_msg = f"Médias de volume base zeradas, mercado ilíquido ou inoperável para o ativo de indexador '{asset}'."
        else:
            surge = ((recent_vol - historical_avg_vol) / historical_avg_vol) * 100
            vol_msg = f"Volume Atual de Negócios: {recent_vol}\nMédia dos Últimos 10 Pregões: {historical_avg_vol:.0f}\nAumento ou Queda de Interesse: {surge:.2f}%\n"
            
        return f"Ativo (Trend Analysis): {asset}\nMetodologia: YFinance Tick Market Volume Anomaly\n{vol_msg}"

    def analyze_trends(self, asset: str) -> AgentSignal:
        real_volume_data = self.fetch_real_volume_data(asset)
        
        prompt = f"Analise em DADOS REAIS o pico de interesse deste ativo na bolsa baseados em volume hoje:\n{real_volume_data}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Groq não retornou JSON em TrendsAgent. Resposta: {response}")
            
        data = json.loads(json_match.group(0))
        
        return AgentSignal(
            agent_name="TrendsAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=real_volume_data
        )
