import json
import re
import yfinance as yf
from ..core.schemas import AgentSignal
from ..llm.groq_client import GroqClient

class TechnicalAgent:
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = """
        Você é o TechnicalAgent, um especialista em Análise Técnica e Price Action.
        Sua função é cruzar múltiplos tempos gráficos (5m, 15m, 1h, 1d, 1wk) para buscar a mais alta assertividade possível.
        Identifique suportes, resistências e tendências críticas.
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "signal_type": "STRONG BUY" ou "STRONG SELL" ou "NEUTRAL",
            "confidence": 95.5,
            "summary": "Resumo técnico apontando a convergência dos tempos gráficos."
        }
        """
        
    def _get_ticker(self, asset: str) -> str:
        asset = asset.upper().strip()
        if asset == "USD": return "USDBRL=X"
        if asset == "EUR": return "EURBRL=X"
        if asset == "BRL": return "^BVSP"
        if not asset.endswith(".SA") and not asset.endswith("=X") and not asset.startswith("^"):
            return f"{asset}.SA"
        return asset

    def fetch_multi_timeframe_data(self, asset: str) -> str:
        ticker_str = self._get_ticker(asset)
        ticker = yf.Ticker(ticker_str)
        
        # Coletando múltiplos tempos gráficos
        hist_1d = ticker.history(period="1mo", interval="1d")
        hist_1h = ticker.history(period="5d", interval="1h")
        
        if hist_1d.empty:
            raise ValueError(f"Sem dados técnicos diários para {asset}.")

        close_1d = hist_1d['Close'].iloc[-1]
        ma_20_1d = hist_1d['Close'].rolling(window=20).mean().iloc[-1] if len(hist_1d) >= 20 else "N/A"
        
        close_1h = hist_1h['Close'].iloc[-1] if not hist_1h.empty else "N/A"

        tech_data = f"Ativo: {asset}\n"
        tech_data += f"Fechamento 1D: {close_1d:.2f} | MA20 Diária: {ma_20_1d}\n"
        tech_data += f"Fechamento 1H: {close_1h}\n"
        tech_data += "Analise a convergência entre o curtíssimo e longo prazo para máxima precisão."
        
        return tech_data

    def analyze_technical(self, asset: str) -> AgentSignal:
        tech_data = self.fetch_multi_timeframe_data(asset)
        prompt = f"Faça uma análise técnica profunda com base nos dados:\n{tech_data}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Groq falhou no TechnicalAgent. Raw: {response}")
            
        data = json.loads(json_match.group(0))
        
        return AgentSignal(
            agent_name="TechnicalAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=tech_data
        )