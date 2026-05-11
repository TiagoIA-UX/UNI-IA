"""Execution Engine Fast — caminho determinístico (sem LLM).

Decide rapidamente uma direção/força de entrada com base em features
puramente numéricas computadas pelo ATLAS para o timeframe do gráfico.

Sem placeholders. Se faltar dado essencial: bloqueia explicitamente.

Saída padronizada:
    {
        "decision": "long" | "short" | "flat" | "block",
        "confidence_pct": 0..100,        # força/precisão observável (real)
        "reasons": [...],                # justificativas determinísticas
        "missing": [...],                # features essenciais ausentes
        "features_used": {...},          # snapshot real (auditoria)
        "strategy_family": str | None,
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.chart_timeframes import (
    aegis_base_weights_for_chart_timeframe,
    normalize_chart_timeframe,
)


# Famílias de estratégia onde o fast path é apropriado (scalping/intraday).
_FAST_PATH_FAMILIES = frozenset({"intraday_swings", "swing_intraday_htf"})

# Limiares determinísticos (ajustáveis por env, sem default escondido).
_RSI_OVERBOUGHT = 70.0
_RSI_OVERSOLD = 30.0
_VOL_RATIO_HOT = 1.5
_GAP_ATR_HOT = 0.6   # gap diário relevante quando >= 0.6 * ATR14
_MIN_CONFIDENCE_TO_EXECUTE = 60.0


def _safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        f = float(val)
    except (TypeError, ValueError):
        return None
    if f != f:
        return None
    return f


def _structure_polarity(structure_trend: Any) -> int:
    s = (str(structure_trend or "")).lower()
    if s == "bullish":
        return 1
    if s == "bearish":
        return -1
    return 0


def _classify_canonical_family(canonical: Optional[str]) -> Optional[str]:
    from core.chart_timeframes import _ROW_BY_CANON

    if not canonical:
        return None
    row = _ROW_BY_CANON.get(canonical)
    if not row:
        return None
    fam = row.get("strategy_family")
    return str(fam) if fam else None


def evaluate_fast_path(
    *,
    atlas_features: Dict[str, Any],
    chart_timeframe: Optional[str],
) -> Dict[str, Any]:
    """Avalia entrada com regras determinísticas (sem LLM)."""
    tf_norm = normalize_chart_timeframe(chart_timeframe) if chart_timeframe else None
    family = _classify_canonical_family(tf_norm)

    if not atlas_features:
        return {
            "decision": "block",
            "confidence_pct": 0.0,
            "reasons": ["atlas_features_ausentes"],
            "missing": ["atlas"],
            "features_used": {},
            "strategy_family": family,
        }

    fast_eligible = family in _FAST_PATH_FAMILIES

    rsi_chart = _safe_float(atlas_features.get("user_chart_tf_rsi14"))
    rsi_1d = _safe_float(atlas_features.get("rsi_14_1d"))
    vol_ratio_chart = _safe_float(atlas_features.get("user_chart_tf_volume_ratio"))
    vol_ratio_1d = _safe_float(atlas_features.get("volume_ratio"))
    structure_chart = atlas_features.get("user_chart_tf_structure_trend")
    structure_1d = atlas_features.get("structure_trend")
    last_return = _safe_float(atlas_features.get("user_chart_tf_last_return_pct"))
    daily_gap_pct = _safe_float(atlas_features.get("daily_session_gap_pct"))
    daily_gap_atr = _safe_float(atlas_features.get("daily_gap_atr_ratio"))
    macd_cross = (str(atlas_features.get("macd_cross") or "")).lower()
    bos = bool(atlas_features.get("structure_bos"))
    atr_regime = (str(atlas_features.get("atr_regime") or "")).lower()

    rsi = rsi_chart if rsi_chart is not None else rsi_1d
    vol_ratio = vol_ratio_chart if vol_ratio_chart is not None else vol_ratio_1d
    structure = structure_chart if structure_chart else structure_1d
    polarity = _structure_polarity(structure)

    reasons: List[str] = []
    missing: List[str] = []
    if rsi is None:
        missing.append("rsi")
    if vol_ratio is None:
        missing.append("volume_ratio")
    if polarity == 0:
        missing.append("structure_trend")

    if missing:
        return {
            "decision": "block",
            "confidence_pct": 0.0,
            "reasons": [f"missing_feature:{m}" for m in missing],
            "missing": missing,
            "features_used": _audit_snapshot(
                rsi=rsi,
                vol_ratio=vol_ratio,
                structure=structure,
                last_return=last_return,
                daily_gap_pct=daily_gap_pct,
                daily_gap_atr=daily_gap_atr,
                macd_cross=macd_cross,
                bos=bos,
                atr_regime=atr_regime,
            ),
            "strategy_family": family,
        }

    direction: str = "flat"
    components: List[Tuple[str, float]] = []

    if polarity > 0:
        direction = "long"
        components.append(("structure_bullish", 25.0))
    elif polarity < 0:
        direction = "short"
        components.append(("structure_bearish", 25.0))

    if direction == "long" and rsi is not None:
        if rsi >= _RSI_OVERBOUGHT:
            components.append(("rsi_overbought_penalty", -15.0))
        elif rsi <= _RSI_OVERSOLD:
            components.append(("rsi_oversold_bounce", 8.0))
        else:
            components.append(("rsi_neutral_ok", 6.0))
    elif direction == "short" and rsi is not None:
        if rsi <= _RSI_OVERSOLD:
            components.append(("rsi_oversold_penalty", -15.0))
        elif rsi >= _RSI_OVERBOUGHT:
            components.append(("rsi_overbought_exhaustion", 8.0))
        else:
            components.append(("rsi_neutral_ok", 6.0))

    if vol_ratio is not None:
        if vol_ratio >= _VOL_RATIO_HOT:
            components.append(("volume_hot", 12.0))
        elif vol_ratio < 0.5:
            components.append(("volume_thin_penalty", -10.0))

    if macd_cross == "bullish" and direction == "long":
        components.append(("macd_bullish_aligned", 8.0))
    elif macd_cross == "bearish" and direction == "short":
        components.append(("macd_bearish_aligned", 8.0))
    elif macd_cross in {"bullish", "bearish"}:
        components.append(("macd_against_direction", -6.0))

    if bos:
        components.append(("break_of_structure", 6.0))

    if atr_regime == "extreme":
        components.append(("atr_extreme_penalty", -12.0))
    elif atr_regime == "high":
        components.append(("atr_high_warn", -4.0))
    elif atr_regime in {"normal", "low"}:
        components.append(("atr_regime_stable", 3.0))

    if daily_gap_atr is not None and daily_gap_atr >= _GAP_ATR_HOT:
        components.append(("daily_gap_significant", -8.0 if direction == "long" else -4.0))

    if last_return is not None:
        if direction == "long" and last_return > 0:
            components.append(("last_bar_aligned_long", 4.0))
        elif direction == "short" and last_return < 0:
            components.append(("last_bar_aligned_short", 4.0))

    base = 50.0
    score = base + sum(weight for _, weight in components)
    score = max(0.0, min(100.0, round(score, 2)))

    if direction == "flat":
        decision = "flat"
        reasons.append("structure_undefined")
    elif not fast_eligible:
        decision = direction
        reasons.append(f"family_not_fast_path:{family}")
        reasons.append("fast_path_advisory_only")
    elif score < _MIN_CONFIDENCE_TO_EXECUTE:
        decision = "block"
        reasons.append(f"score_below_min:{score}<{_MIN_CONFIDENCE_TO_EXECUTE}")
    else:
        decision = direction

    reasons.extend(f"{name}({weight:+.1f})" for name, weight in components)

    return {
        "decision": decision,
        "confidence_pct": score,
        "reasons": reasons,
        "missing": missing,
        "features_used": _audit_snapshot(
            rsi=rsi,
            vol_ratio=vol_ratio,
            structure=structure,
            last_return=last_return,
            daily_gap_pct=daily_gap_pct,
            daily_gap_atr=daily_gap_atr,
            macd_cross=macd_cross,
            bos=bos,
            atr_regime=atr_regime,
        ),
        "strategy_family": family,
        "weights_template": aegis_base_weights_for_chart_timeframe(tf_norm),
    }


def _audit_snapshot(**kwargs: Any) -> Dict[str, Any]:
    return {k: v for k, v in kwargs.items() if v is not None and v != ""}
