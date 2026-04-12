import json
import re
from ..core.schemas import AgentSignal
from ..llm.groq_client import GroqClient

class SentimentAgent:
    def __init__(self):
        self.llm = GroqClient()
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

    def analyze_sentiment(self, asset: str, news_data: str) -> AgentSignal:
        prompt = f"Faça análise de sentimento das notícias extraídas da web hoje para o ativo {asset}:\n{news_data}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"O Groq não retornou JSON válido em SentimentAgent. Resposta: {response}")
            
        data = json.loads(json_match.group(0))
        
        return AgentSignal(
            agent_name="SentimentAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"]
        )
