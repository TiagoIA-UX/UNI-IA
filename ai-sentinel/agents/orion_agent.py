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
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from core.feature_store import FeatureStore
from core.schemas import AgentSignal, LlmProvenance
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
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")[:10]
        except Exception:
            return []
        if not items:
            return []
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

    def _classify_single_news(
        self, asset: str, news_item: Dict[str, str]
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Classifica uma manchete. Segundo valor: None OK, 'groq' falha API, 'parse' JSON invalido."""
        prompt = f"Ativo: {asset}\nNoticia: {news_item['title']}\nData: {news_item['pub_date']}"
        fallback = {
            "polarity": "NEUTRAL",
            "impact_score": 0,
            "surprise_level": "NONE",
            "impact_horizon": "medium_term",
            "category": "other",
            "summary": "Classificacao indisponivel (Groq ou rede).",
        }
        try:
            comp = self.llm.complete(self.classification_prompt, prompt)
        except RuntimeError:
            fb = dict(fallback)
            fb["summary"] = "Classificacao indisponivel (Groq ou rede)."
            return fb, "groq"
        try:
            return extract_json_object(comp.text), None
        except Exception:
            fb = dict(fallback)
            fb["summary"] = "Falha na classificacao."
            return fb, "parse"
    # ------------------------------------------------------------------
    # Feature computation
    # ------------------------------------------------------------------

    def compute_features(self, asset: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Busca noticias, classifica cada uma, consolida features numericas."""
        raw_news = self._fetch_news(asset)
        if not raw_news:
            empty_features: Dict[str, Any] = {
                "asset": asset,
                "news_total": 0,
                "news_positive": 0,
                "news_negative": 0,
                "news_neutral": 0,
                "sentiment_score": 0.0,
                "avg_impact_score": 0.0,
                "max_impact_score": 0.0,
                "surprise_ratio_pct": 0.0,
                "high_surprise_count": 0,
                "horizon_immediate": 0,
                "horizon_short_term": 0,
                "horizon_medium_term": 0,
                "dominant_category": "other",
                "category_distribution": {},
                "news_feed_status": "empty_or_unavailable",
                "groq_classify_failures": 0,
                "classify_parse_failures": 0,
            }
            return empty_features, []

        classifications: List[Dict[str, Any]] = []
        groq_classify_failures = 0
        classify_parse_failures = 0

        for item in raw_news:
            classification, fail_tag = self._classify_single_news(asset, item)
            if fail_tag == "groq":
                groq_classify_failures += 1
            elif fail_tag == "parse":
                classify_parse_failures += 1
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
            "news_feed_status": "ok",
            "groq_classify_failures": groq_classify_failures,
            "classify_parse_failures": classify_parse_failures,
            "news_total": total,            "news_positive": positive,
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

    @staticmethod
    def _synthesis_fallback_from_features(features: Dict[str, Any]) -> Dict[str, Any]:
        """Quando a sintese LLM falha mas ja ha features numericas."""
        sentiment = float(features.get("sentiment_score") or 0)
        if sentiment > 12:
            signal_type = "BULLISH"
            regime = "RISK-ON"
        elif sentiment < -12:
            signal_type = "BEARISH"
            regime = "RISK-OFF"
        else:
            signal_type = "NEUTRAL"
            regime = "TRANSITIONAL"
        conf = min(88.0, 45.0 + min(abs(sentiment), 40.0))
        return {
            "signal_type": signal_type,
            "confidence": conf,
            "regime": regime,
            "regime_shift_probability": float(features.get("surprise_ratio_pct") or 0),
            "summary": (
                "Sintese LLM indisponivel; julgamento aproximado a partir das features "
                f"(sentiment_score={sentiment:.1f}, surpresa={features.get('surprise_ratio_pct', 0)}%)."
            ),
        }

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyze(self, asset: str, signal_id: Optional[str] = None, strategy_legenda: Optional[str] = None) -> AgentSignal:
        """Busca noticias, classifica, computa features, persiste, sintetiza."""
        features, classifications = self.compute_features(asset)

        orion_llm: Optional[LlmProvenance] = None

        if not features.get("news_total"):
            data = {
                "signal_type": "NEUTRAL",
                "confidence": 40.0,
                "regime": "TRANSITIONAL",
                "regime_shift_probability": 0.0,
                "summary": (
                    "Nenhuma manchete recuperada do feed de noticias (RSS vazio ou indisponivel); "
                    "contexto de noticias tratado como neutro."
                ),
            }
            orion_llm = LlmProvenance(
                provider="none",
                model=None,
                status="llm_skipped",
                detail="no_rss_headlines",
            )
        else:
            feature_text = self._format_features(features)
            prompt = f"Vetor de features de noticias para {asset}:\n\n{feature_text}\n\nSintetize o contexto narrativo."
            if strategy_legenda:
                prompt = f"[Contexto por timeframe]\n{strategy_legenda}\n\n{prompt}"

            classify_groq_failed = int(features.get("groq_classify_failures") or 0)
            classify_parse_failed = int(features.get("classify_parse_failures") or 0)
            synthesis_model: Optional[str] = None
            synthesis_status = "llm_success"
            synthesis_detail = "per_headline_classify_plus_synthesis"

            try:
                comp = self.llm.complete(self.synthesis_prompt, prompt)
                data = extract_json_object(comp.text)
                synthesis_model = comp.model
            except RuntimeError:
                data = self._synthesis_fallback_from_features(features)
                synthesis_status = "llm_fallback"
                synthesis_detail = "synthesis_groq_failed_rule_based"
            except Exception:
                data = self._synthesis_fallback_from_features(features)
                synthesis_status = "llm_fallback"
                synthesis_detail = "synthesis_parse_or_unknown_rule_based"

            if classify_groq_failed or classify_parse_failed:
                if synthesis_status == "llm_success":
                    synthesis_status = "llm_partial"
                synthesis_detail = (
                    f"classify_groq_failed={classify_groq_failed},"
                    f"classify_parse_failed={classify_parse_failed};{synthesis_detail}"
                )

            orion_llm = LlmProvenance(
                provider="groq",
                model=synthesis_model or str(self.llm.model),
                status=synthesis_status,
                detail=synthesis_detail,
            )
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
            llm_provenance=orion_llm,
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
