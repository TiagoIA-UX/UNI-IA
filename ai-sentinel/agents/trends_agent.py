from typing import Optional

import yfinance as yf
from agents.market_utils import resolve_market_ticker
from core.feature_store import FeatureStore
from core.schemas import AgentSignal
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object

class TrendsAgent:
    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.llm = GroqClient()
        self.feature_store = feature_store or FeatureStore()
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
        return resolve_market_ticker(asset)

    def fetch_real_volume_data(self, asset: str) -> dict:
        ticker_str = self._get_ticker(asset)
        ticker = yf.Ticker(ticker_str)
        hist = ticker.history(period="15d")
        
        if hist.empty or 'Volume' not in hist.columns:
            raise ValueError(f"Não há dados recentes de volume de Ticker para Trends no YFinance ({ticker_str}) para o ativo {asset}")
            
        recent_vol = hist["Volume"].iloc[-1]
        historical_avg_vol = hist["Volume"].iloc[-10:-1].mean() if len(hist) > 10 else recent_vol
        
        if historical_avg_vol <= 0:
            surge = 0.0
            vol_msg = f"Médias de volume base zeradas, mercado ilíquido ou inoperável para o ativo de indexador '{asset}'."
        else:
            surge = ((recent_vol - historical_avg_vol) / historical_avg_vol) * 100
            vol_msg = f"Volume Atual de Negócios: {recent_vol}\nMédia dos Últimos 10 Pregões: {historical_avg_vol:.0f}\nAumento ou Queda de Interesse: {surge:.2f}%\n"
        return {
            "asset": asset,
            "ticker": ticker_str,
            "recent_volume": float(recent_vol),
            "avg_volume_10d": float(historical_avg_vol),
            "volume_surge_pct": round(float(surge), 6),
            "raw_text": f"Ativo (Trend Analysis): {asset}\nMetodologia: YFinance Tick Market Volume Anomaly\n{vol_msg}",
        }

    def analyze_trends(self, asset: str, signal_id: Optional[str] = None, strategy_legenda: Optional[str] = None) -> AgentSignal:
        volume_features = self.fetch_real_volume_data(asset)
        real_volume_data = volume_features["raw_text"]
        
        prompt = f"Analise em DADOS REAIS o pico de interesse deste ativo na bolsa baseados em volume hoje:\n{real_volume_data}"
        if strategy_legenda:
            prompt = f"[Contexto por timeframe]\n{strategy_legenda}\n\n{prompt}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        data = extract_json_object(response)

        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="TrendsAgent",
                features={
                    "recent_volume": volume_features["recent_volume"],
                    "avg_volume_10d": volume_features["avg_volume_10d"],
                    "volume_surge_pct": volume_features["volume_surge_pct"],
                    "emitted_confidence": float(data["confidence"]),
                },
                metadata={
                    "signal_type": data["signal_type"],
                    "summary": data["summary"],
                },
            )
        
        return AgentSignal(
            agent_name="TrendsAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=real_volume_data
        )
