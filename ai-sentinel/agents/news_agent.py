import urllib.parse
from typing import Optional

import requests
from bs4 import BeautifulSoup
from core.feature_store import FeatureStore
from core.schemas import AgentSignal
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object

class NewsAgent:
    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.llm = GroqClient()
        self.feature_store = feature_store or FeatureStore()
        self.system_prompt = """
        Você é o NewsAgent. Sua função é analisar um conjunto de NOTÍCIAS REAIS e recentes.
        Identifique o impacto principal para o ativo.
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "signal_type": "BULLISH" ou "BEARISH" ou "NEUTRAL",
            "confidence": 85.5,
            "summary": "Resumo das notícias e o provável impacto no ativo."
        }
        """

    def fetch_real_news(self, asset: str) -> dict:
        # Busca notícias reais no Google News RSS
        query = urllib.parse.quote(f"{asset} mercado financeiro economia")
        url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Sem fallback. Se falhar, estoura erro!
        
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")[:7] # Top 7 notícias reais mais recentes
        
        if not items:
            raise ValueError(f"Nenhuma notícia encontrada para {asset}.")
            
        headlines = [item.title.text for item in items]
        pub_dates = [item.pubDate.text for item in items if item.pubDate and item.pubDate.text]
        news_text = "\n".join([f"- Título: {title}" for title in headlines])
        avg_title_length = sum(len(title) for title in headlines) / len(headlines)
        longest_title_length = max(len(title) for title in headlines)
        return {
            "raw_text": news_text,
            "headlines": headlines,
            "headline_count": len(headlines),
            "avg_title_length": round(avg_title_length, 4),
            "longest_title_length": float(longest_title_length),
            "has_publication_date": bool(pub_dates),
        }

    def analyze_news(self, asset: str, signal_id: Optional[str] = None, strategy_legenda: Optional[str] = None) -> AgentSignal:
        news_data = self.fetch_real_news(asset)
        raw_news = news_data["raw_text"]
        prompt = f"Analise as seguintes NOTÍCIAS REAIS de hoje para o ativo {asset}:\n{raw_news}"
        if strategy_legenda:
            prompt = f"[Contexto por timeframe]\n{strategy_legenda}\n\n{prompt}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        # Extrai JSON sem placeholders
        data = extract_json_object(response)

        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="NewsAgent",
                features={
                    "headline_count": news_data["headline_count"],
                    "avg_title_length": news_data["avg_title_length"],
                    "longest_title_length": news_data["longest_title_length"],
                    "has_publication_date": news_data["has_publication_date"],
                    "emitted_confidence": float(data["confidence"]),
                },
                metadata={
                    "signal_type": data["signal_type"],
                    "summary": data["summary"],
                    "headlines": news_data["headlines"],
                },
            )
        
        return AgentSignal(
            agent_name="NewsAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            # Armazenamos a notícia raw_news no summary temporariamente para o SentimentAgent poder ler depois
            raw_data=raw_news 
        )
