import json
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from ..core.schemas import AgentSignal
from ..llm.groq_client import GroqClient

class NewsAgent:
    def __init__(self):
        self.llm = GroqClient()
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

    def fetch_real_news(self, asset: str) -> str:
        # Busca notícias reais no Google News RSS
        query = urllib.parse.quote(f"{asset} mercado financeiro economia")
        url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Sem fallback. Se falhar, estoura erro!
        
        soup = BeautifulSoup(response.content, "xml")
        items = soup.find_all("item")[:7] # Top 7 notícias reais mais recentes
        
        if not items:
            raise ValueError(f"Nenhuma notícia encontrada para {asset}.")
            
        news_text = "\n".join([f"- Título: {item.title.text} (Data: {item.pubDate.text})" for item in items])
        return news_text

    def analyze_news(self, asset: str) -> AgentSignal:
        raw_news = self.fetch_real_news(asset)
        prompt = f"Analise as seguintes NOTÍCIAS REAIS de hoje para o ativo {asset}:\n{raw_news}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        # Extrai JSON sem placeholders
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"O Groq não retornou um JSON válido. Resposta: {response}")
            
        data = json.loads(json_match.group(0))
        
        return AgentSignal(
            agent_name="NewsAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            # Armazenamos a notícia raw_news no summary temporariamente para o SentimentAgent poder ler depois
            raw_data=raw_news 
        )
