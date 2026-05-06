"""ORION — Agente Cognitivo de Noticias.

ORION nao olha candle. ORION olha narrativa.

Features computadas:
  - Contagem de noticias por polaridade
  - Score de impacto ponderado
  - Deteccao de surpresa (divergencia entre consenso e noticia)
  - Classificacao de regime (risk-on / risk-off / transitional)
  - Horizonte de impacto estimado

Busca noticias reais (Google News RSS).
Classifica cada noticia individualmente antes de consolidar.
Persiste features no FeatureStore.
"""

import urllib.parse
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from core.feature_store import FeatureStore
from core.schemas import AgentSignal
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object


class OrionAgent:
    """Agente Cognitivo de Noticias — ORION."""

    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.llm = GroqClient()
        self.feature_store = feature_store or FeatureStore()

        self.classification_prompt = """Voce e o ORION, agente cognitivo de noticias do Zairyx IA.
Voce recebe UMA noticia de cada vez e classifica o impacto dela para o ativo.

Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "polarity": "POSITIVE" ou "NEGATIVE" ou "NEUTRAL",
    "impact_score": 75,
    "surprise_level": "HIGH" ou "MEDIUM" ou "LOW" ou "NONE",
    "impact_horizon": "immediate" ou "short_term" ou "medium_term",
    "category": "earnings" ou "macro_policy" ou "geopolitical" ou "sector" ou "technical" ou "regulatory" ou "other",
    "summary": "Resumo do impacto em uma frase."
}

Regras:
- impact_score: 0-100, quanto maior mais relevante para decisao.
- surprise_level: o quao inesperada e a noticia vs consenso de mercado.
- impact_horizon: immediate (<4h), short_term (1-3 dias), medium_term (1-4 semanas).
- Seja preciso e objetivo."""

        self.synthesis_prompt = """Voce e o ORION, agente cognitivo de noticias do Zairyx IA.
Voce recebe um VETOR NUMERICO consolidado de features de noticias ja classificadas.
Sua funcao e sintetizar o contexto macro-narrativo e emitir julgamento.

Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "signal_type": "BULLISH" ou "BEARISH" ou "NEUTRAL",
    "confidence": 82.0,
    "regime": "RISK-ON" ou "RISK-OFF" ou "TRANSITIONAL",
    "regime_shift_probability": 25.0,
    "summary": "Sintese do contexto narrativo e impacto provavel no ativo."
}"""

    # ------------------------------------------------------------------
    # News fetching
    # ------------------------------------------------------------------

    def _fetch_news(self, asset: str) -> List[Dict[str, str]]:
        query = urllib.parse.quote(f"{asset} mercado financeiro economia")
        url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

        resp = requests.get(url, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")[:10]

        if not items:
            raise ValueError(f"Nenhuma noticia encontrada para {asset}.")

        return [
            {
                "title": item.title.text if item.title else "",
                "pub_date": item.pubDate.text if item.pubDate else "",
            }
            for item in items
        ]

    # ------------------------------------------------------------------
    # Per-news classification
    # ------------------------------------------------------------------

    def _classify_single_news(self, asset: str, news_item: Dict[str, str]) -> Dict[str, Any]:
        prompt = f"Ativo: {asset}\nNoticia: {news_item['title']}\nData: {news_item['pub_date']}"
        response = self.llm.generate_response(self.classification_prompt, prompt)
        try:
            return extract_json_object(response)
        except Exception:
            return {
                "polarity": "NEUTRAL",
                "impact_score": 0,
                "surprise_level": "NONE",
                "impact_horizon": "medium_term",
                "category": "other",
                "summary": "Falha na classificacao.",
            }

    # ------------------------------------------------------------------
    # Feature computation
    # ------------------------------------------------------------------

    def compute_features(self, asset: str) -> Dict[str, Any]:
        """Busca noticias, classifica cada uma, consolida features numericas."""
        raw_news = self._fetch_news(asset)
        classifications: List[Dict[str, Any]] = []

        for item in raw_news:
            classification = self._classify_single_news(asset, item)
            classification["title"] = item["title"]
            classifications.append(classification)

        # Aggregate features
        total = len(classifications)
        positive = sum(1 for c in classifications if c.get("polarity") == "POSITIVE")
        negative = sum(1 for c in classifications if c.get("polarity") == "NEGATIVE")
        neutral = total - positive - negative

        scores = [float(c.get("impact_score", 0)) for c in classifications]
        avg_impact = sum(scores) / total if total > 0 else 0.0
        max_impact = max(scores) if scores else 0.0

        # Weighted sentiment score: +1 positive, -1 negative, 0 neutral, weighted by impact_score
        weighted_sentiment = 0.0
        total_weight = 0.0
        for c in classifications:
            weight = float(c.get("impact_score", 0))
            if c.get("polarity") == "POSITIVE":
                weighted_sentiment += weight
            elif c.get("polarity") == "NEGATIVE":
                weighted_sentiment -= weight
            total_weight += weight
        sentiment_score = round(weighted_sentiment / total_weight * 100, 2) if total_weight > 0 else 0.0

        # Surprise detection
        high_surprise = sum(1 for c in classifications if c.get("surprise_level") in ("HIGH", "MEDIUM"))
        surprise_ratio = round(high_surprise / total * 100, 2) if total > 0 else 0.0

        # Impact horizon distribution
        immediate_count = sum(1 for c in classifications if c.get("impact_horizon") == "immediate")
        short_count = sum(1 for c in classifications if c.get("impact_horizon") == "short_term")
        medium_count = sum(1 for c in classifications if c.get("impact_horizon") == "medium_term")

        # Category distribution
        categories = {}
        for c in classifications:
            cat = c.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1

        features = {
            "asset": asset,
            "news_total": total,
            "news_positive": positive,
            "news_negative": negative,
            "news_neutral": neutral,
            "sentiment_score": sentiment_score,
            "avg_impact_score": round(avg_impact, 2),
            "max_impact_score": round(max_impact, 2),
            "surprise_ratio_pct": surprise_ratio,
            "high_surprise_count": high_surprise,
            "horizon_immediate": immediate_count,
            "horizon_short_term": short_count,
            "horizon_medium_term": medium_count,
            "dominant_category": max(categories, key=categories.get) if categories else "other",
            "category_distribution": categories,
        }

        return features, classifications

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze(self, asset: str, signal_id: Optional[str] = None) -> AgentSignal:
        """Busca noticias, classifica, computa features, persiste, sintetiza."""
        features, classifications = self.compute_features(asset)

        # Synthesis via LLM (on top of computed features, not raw text)
        feature_text = self._format_features(features)
        prompt = f"Vetor de features de noticias para {asset}:\n\n{feature_text}\n\nSintetize o contexto narrativo."

        response = self.llm.generate_response(self.synthesis_prompt, prompt)
        data = extract_json_object(response)

        # Enrich features with regime
        features["regime"] = data.get("regime", "TRANSITIONAL")
        features["regime_shift_probability"] = data.get("regime_shift_probability", 0.0)

        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="ORION",
                features={
                    **features,
                    "emitted_confidence": float(data["confidence"]),
                },
                metadata={
                    "signal_type": data["signal_type"],
                    "summary": data["summary"],
                    "headlines": [c.get("title", "") for c in classifications[:7]],
                },
            )

        raw_headlines = "\n".join([f"- {c.get('title', '')}" for c in classifications[:7]])

        return AgentSignal(
            agent_name="ORION",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=raw_headlines,
        )

    def _format_features(self, features: Dict[str, Any]) -> str:
        lines = []
        for key, val in features.items():
            if key == "asset":
                continue
            if val is None:
                continue
            lines.append(f"  {key}: {val}")
        return "\n".join(lines)
