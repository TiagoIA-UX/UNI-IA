from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RegimeContext:
    regime_id: str
    regime_label: str
    regime_version: str
    regime_confidence: float
    volatility_regime: str
    market_structure: str
    liquidity_regime: str
    macro_regime: str
    news_regime: str
    event_pressure: str
    regime_features: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regime_id": self.regime_id,
            "regime_label": self.regime_label,
            "regime_version": self.regime_version,
            "regime_confidence": self.regime_confidence,
            "volatility_regime": self.volatility_regime,
            "market_structure": self.market_structure,
            "liquidity_regime": self.liquidity_regime,
            "macro_regime": self.macro_regime,
            "news_regime": self.news_regime,
            "event_pressure": self.event_pressure,
            "regime_features": self.regime_features,
        }


class RegimeEngine:
    VERSION = "regime_engine.v1"

    def classify(
        self,
        *,
        asset: str,
        macro_signal,
        atlas_signal,
        orion_signal,
        news_signal,
        macro_features: Optional[Dict[str, Any]] = None,
        atlas_features: Optional[Dict[str, Any]] = None,
        orion_features: Optional[Dict[str, Any]] = None,
        news_features: Optional[Dict[str, Any]] = None,
    ) -> RegimeContext:
        atlas_features = atlas_features or {}
        orion_features = orion_features or {}
        macro_features = macro_features or {}
        news_features = news_features or {}

        volatility_regime = str(atlas_features.get("atr_regime") or "unknown")
        market_structure = str(atlas_features.get("structure_trend") or "unknown")
        liquidity_regime = self._classify_liquidity(news_features=news_features, macro_features=macro_features)
        macro_regime = self._normalize_macro_signal(getattr(macro_signal, "signal_type", None))
        news_regime = str(orion_features.get("regime") or "TRANSITIONAL").upper()
        event_pressure = self._classify_event_pressure(orion_features)

        regime_id = self._determine_regime_id(
            volatility_regime=volatility_regime,
            market_structure=market_structure,
            liquidity_regime=liquidity_regime,
            macro_regime=macro_regime,
            news_regime=news_regime,
            event_pressure=event_pressure,
        )
        regime_label = self._human_label(regime_id)
        regime_confidence = self._confidence(
            regime_id=regime_id,
            macro_signal=macro_signal,
            atlas_signal=atlas_signal,
            orion_signal=orion_signal,
            news_signal=news_signal,
            event_pressure=event_pressure,
        )

        regime_features = {
            "asset": asset,
            "volatility_regime": volatility_regime,
            "market_structure": market_structure,
            "liquidity_regime": liquidity_regime,
            "macro_regime": macro_regime,
            "news_regime": news_regime,
            "event_pressure": event_pressure,
            "macro_confidence": float(getattr(macro_signal, "confidence", 0.0) or 0.0),
            "atlas_confidence": float(getattr(atlas_signal, "confidence", 0.0) or 0.0),
            "orion_confidence": float(getattr(orion_signal, "confidence", 0.0) or 0.0),
            "news_confidence": float(getattr(news_signal, "confidence", 0.0) or 0.0),
            "news_sentiment_score": orion_features.get("sentiment_score"),
            "news_surprise_ratio_pct": orion_features.get("surprise_ratio_pct"),
            "high_surprise_count": orion_features.get("high_surprise_count"),
            "macro_daily_variation_pct": macro_features.get("daily_variation_pct"),
            "news_headline_count": news_features.get("headline_count"),
        }

        return RegimeContext(
            regime_id=regime_id,
            regime_label=regime_label,
            regime_version=self.VERSION,
            regime_confidence=regime_confidence,
            volatility_regime=volatility_regime,
            market_structure=market_structure,
            liquidity_regime=liquidity_regime,
            macro_regime=macro_regime,
            news_regime=news_regime,
            event_pressure=event_pressure,
            regime_features=regime_features,
        )

    def _classify_liquidity(self, *, news_features: Dict[str, Any], macro_features: Dict[str, Any]) -> str:
        recent_volume = macro_features.get("recent_volume")
        headline_count = float(news_features.get("headline_count") or 0.0)
        if recent_volume is None:
            if headline_count >= 5:
                return "attention_rich"
            return "unknown"
        if float(recent_volume) <= 0:
            return "vacuum"
        if headline_count >= 7:
            return "attention_rich"
        return "normal"

    def _normalize_macro_signal(self, signal_type: Any) -> str:
        normalized = str(signal_type or "NEUTRAL").upper().strip()
        if normalized not in {"RISK-ON", "RISK-OFF", "NEUTRAL"}:
            return "NEUTRAL"
        return normalized

    def _classify_event_pressure(self, orion_features: Dict[str, Any]) -> str:
        high_surprise_count = float(orion_features.get("high_surprise_count") or 0.0)
        surprise_ratio = float(orion_features.get("surprise_ratio_pct") or 0.0)
        if high_surprise_count >= 3 or surprise_ratio >= 70.0:
            return "high"
        if high_surprise_count >= 1 or surprise_ratio >= 35.0:
            return "moderate"
        return "low"

    def _determine_regime_id(
        self,
        *,
        volatility_regime: str,
        market_structure: str,
        liquidity_regime: str,
        macro_regime: str,
        news_regime: str,
        event_pressure: str,
    ) -> str:
        volatility_regime = volatility_regime.lower()
        market_structure = market_structure.lower()

        if event_pressure == "high":
            return "event_driven"
        if liquidity_regime == "vacuum":
            return "liquidity_stress"
        if market_structure == "bullish" and macro_regime == "RISK-ON" and news_regime == "RISK-ON":
            return "trend_risk_on"
        if market_structure == "bearish" and (macro_regime == "RISK-OFF" or news_regime == "RISK-OFF"):
            return "trend_risk_off"
        if market_structure in {"neutral", "mixed", "compression"}:
            return "range_bound"
        if volatility_regime in {"high", "extreme"}:
            return "volatile_transition"
        return "transition_mixed"

    def _human_label(self, regime_id: str) -> str:
        labels = {
            "event_driven": "Evento macro dominante",
            "liquidity_stress": "Stress de liquidez",
            "trend_risk_on": "Tendencia com apetite a risco",
            "trend_risk_off": "Tendencia defensiva",
            "range_bound": "Range / lateralidade",
            "volatile_transition": "Transicao volatil",
            "transition_mixed": "Transicao mista",
        }
        return labels.get(regime_id, "Regime desconhecido")

    def _confidence(self, *, regime_id: str, macro_signal, atlas_signal, orion_signal, news_signal, event_pressure: str) -> float:
        confidence = (
            float(getattr(macro_signal, "confidence", 0.0) or 0.0)
            + float(getattr(atlas_signal, "confidence", 0.0) or 0.0)
            + float(getattr(orion_signal, "confidence", 0.0) or 0.0)
            + float(getattr(news_signal, "confidence", 0.0) or 0.0)
        ) / 4.0
        if regime_id in {"trend_risk_on", "trend_risk_off", "event_driven"}:
            confidence += 5.0
        if event_pressure == "high":
            confidence += 3.0
        return round(min(max(confidence, 0.0), 100.0), 4)