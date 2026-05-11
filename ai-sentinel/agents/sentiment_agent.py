from typing import Optional

from core.feature_store import FeatureStore
from core.schemas import AgentSignal
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object

class SentimentAgent:
    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.llm = GroqClient()
        self.feature_store = feature_store or FeatureStore()
        self.system_prompt = """
        Você é o SentimentAgent. Sua função é avaliar o tom emocional, psicológico e viés de sentimento de uma série de textos (manchetes de notícias).
        Identifique o medo, pânico, euforia e incerteza (VIX psicológico).
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "signal_type": "POSITIVE" ou "NEGATIVE" ou "NEUTRAL",
            "confidence": 92.5,
            "summary": "Resumo analítico focado na emoção do mercado."
        }
        """

    def analyze_sentiment(
        self,
        asset: str,
        news_data: str,
        signal_id: Optional[str] = None,
        strategy_legenda: Optional[str] = None,
    ) -> AgentSignal:
        prompt = f"Faça análise de sentimento das notícias extraídas da web hoje para o ativo {asset}:\n{news_data}"
        if strategy_legenda:
            prompt = f"[Contexto por timeframe]\n{strategy_legenda}\n\n{prompt}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        data = extract_json_object(response)

        headlines = [line.strip() for line in str(news_data).splitlines() if line.strip()]
        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="SentimentAgent",
                features={
                    "headline_count": len(headlines),
                    "news_text_length": float(len(str(news_data))),
                    "avg_headline_length": round(sum(len(line) for line in headlines) / len(headlines), 4) if headlines else 0.0,
                    "emitted_confidence": float(data["confidence"]),
                },
                metadata={
                    "signal_type": data["signal_type"],
                    "summary": data["summary"],
                },
            )
        
        return AgentSignal(
            agent_name="SentimentAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"]
        )
