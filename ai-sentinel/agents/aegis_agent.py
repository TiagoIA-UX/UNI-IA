"""AEGIS — Agente de Fusao Ponderada.

AEGIS e o comite. Recebe saida do ATLAS e ORION, aplica pesos
dinâmicos baseados em historico de performance, e decide bias final.

Diferenca do antigo StrategyEngine:
  - Pesos sao recalibraveis via performance real (OutcomeTracker)
  - Conflito explícito: se ATLAS e ORION divergem, AEGIS pode ir flat
  - Persiste sua propria decisao no FeatureStore
"""

import os
from typing import Any, Dict, List, Optional

from core.chart_timeframes import (
    DEFAULT_AEGIS_WEIGHTS,
    aegis_base_weights_for_chart_timeframe,
    normalize_chart_timeframe,
    timeframe_strategy_legenda,
)
from core.contract_validation import (
    normalize_classification,
    normalize_confluence_level,
    normalize_direction,
    require_non_empty_string,
    require_percentage,
    validate_required_keys,
)
from core.feature_store import FeatureStore
from core.outcome_tracker import OutcomeTracker
from core.regime_engine import RegimeContext
from core.schemas import AgentSignal, OpportunityAlert, StrategyDecision
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object


class AegisAgent:
    """Agente de Fusao — AEGIS."""

    def __init__(
        self,
        feature_store: Optional[FeatureStore] = None,
        outcome_tracker: Optional[OutcomeTracker] = None,
    ):
        self.feature_store = feature_store or FeatureStore()
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.llm = GroqClient()
        self.default_mode = os.getenv("STRATEGY_DEFAULT_MODE", "swing").lower()

        # Pesos base default (timeframe None / desconhecido); por TF ver aegis_base_weights_for_chart_timeframe.
        self._base_weights = dict(DEFAULT_AEGIS_WEIGHTS)

        self.system_prompt = """Voce e o AEGIS, agente de fusao do Zairyx IA.
Voce recebe sinais dos agentes ATLAS (estrutural) e ORION (narrativo),
junto com o bias ponderado calculado e metricas de performance historica.

Sua funcao e emitir o julgamento final consolidado.

Regras:
1. Se ATLAS e ORION estao ALINHADOS, confianca alta.
2. Se ATLAS e ORION DIVERGEM, confianca reduzida ou FLAT.
3. Se um agente tem win_rate muito superior, dar mais peso a ele.
4. NUNCA ignore o risk filter — se regime = RISK-OFF, seja conservador.

Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "score": 82.0,
    "classification": "OPORTUNIDADE" ou "ATENCAO" ou "RISCO",
    "direction": "long" ou "short" ou "flat",
    "explanation": "Justificativa da fusao.",
    "confluence_level": "strong" ou "moderate" ou "weak" ou "conflicting"
}"""

    # ------------------------------------------------------------------
    # Dynamic weight recalibration
    # ------------------------------------------------------------------

    def _get_effective_weights(
        self,
        regime_context: Optional[RegimeContext] = None,
        chart_timeframe: Optional[str] = None,
    ) -> Dict[str, float]:
        """Recalibra pesos baseado em performance real dos ultimos 30 dias."""
        tf = normalize_chart_timeframe(chart_timeframe) if chart_timeframe else None
        weights = dict(aegis_base_weights_for_chart_timeframe(tf))

        try:
            perf = self.outcome_tracker.compute_performance(window_days=30)
        except Exception as exc:
            raise RuntimeError(f"AEGIS nao conseguiu carregar historico de performance: {exc}") from exc

        if not perf.get("success"):
            raise RuntimeError("AEGIS recebeu payload invalido do OutcomeTracker.")

        if perf["totals"]["trades"] < 10:
            return weights

        if os.getenv("AEGIS_ENABLE_DYNAMIC_RECALIBRATION", "false").strip().lower() != "true":
            return weights

        lookback_days = int(os.getenv("AEGIS_RECALIBRATION_WINDOW_DAYS", "90"))
        min_samples = int(os.getenv("AEGIS_RECALIBRATION_MIN_SAMPLES", "5"))
        recalibration = self.feature_store.compute_agent_weight_recommendations(
            outcome_tracker=self.outcome_tracker,
            window_days=lookback_days,
            min_samples=min_samples,
            regime_id=regime_context.regime_id if regime_context else None,
            regime_version=regime_context.regime_version if regime_context else None,
        )
        recommended_weights = recalibration.get("weights", {})
        if not recommended_weights:
            return weights

        blended_weights: Dict[str, float] = {}
        for agent_name, base_weight in weights.items():
            recommended = float(recommended_weights.get(agent_name, base_weight))
            blended_weights[agent_name] = (float(base_weight) + recommended) / 2.0

        total_weight = sum(blended_weights.values())
        if total_weight <= 0:
            raise RuntimeError("AEGIS recalibrado com soma de pesos invalida.")

        return {
            agent_name: round(weight / total_weight, 6)
            for agent_name, weight in blended_weights.items()
        }

    # ------------------------------------------------------------------
    # Polarity / Direction helpers
    # ------------------------------------------------------------------

    def _polarity(self, signal_type: str) -> float:
        normalized = (signal_type or "").upper()
        positive = ["BUY", "STRONG BUY", "BULL", "BULLISH", "POSITIVE", "RISK-ON", "FOMO", "UNDERVALUED"]
        negative = ["SELL", "STRONG SELL", "BEAR", "BEARISH", "NEGATIVE", "RISK-OFF", "FEAR", "OVERVALUED"]
        if any(token in normalized for token in positive):
            return 1.0
        if any(token in normalized for token in negative):
            return -1.0
        return 0.0

    def _timeframe(self, mode: str) -> str:
        mapping = {
            "day_trade": "15m-1h",
            "swing": "4h-1d",
            "position": "1d-1w",
            "portfolio": "1w-1mo",
        }
        return mapping.get(mode, "4h-1d")

    # ------------------------------------------------------------------
    # Fusion
    # ------------------------------------------------------------------

    def fuse(
        self,
        asset: str,
        signals: List[AgentSignal],
        signal_id: Optional[str] = None,
        regime_context: Optional[RegimeContext] = None,
        chart_timeframe: Optional[str] = None,
    ) -> OpportunityAlert:
        """Fusao ponderada dos sinais dos agentes."""
        weights = self._get_effective_weights(regime_context=regime_context, chart_timeframe=chart_timeframe)

        # Compute weighted bias
        weighted_bias = 0.0
        total_weight = 0.0
        reasons: List[str] = []
        agent_summary: Dict[str, Dict[str, Any]] = {}

        for sig in signals:
            polarity = self._polarity(sig.signal_type)
            weight = weights.get(sig.agent_name, 0.0)
            contribution = polarity * weight * (float(sig.confidence) / 100.0)
            weighted_bias += contribution
            total_weight += weight

            agent_summary[sig.agent_name] = {
                "signal_type": sig.signal_type,
                "confidence": sig.confidence,
                "weight": weight,
                "contribution": round(contribution, 4),
            }

            if sig.summary:
                reasons.append(f"{sig.agent_name}: {sig.summary}")

        # Normalize bias to -100..+100
        if total_weight > 0:
            normalized_bias = round((weighted_bias / total_weight) * 100, 2)
        else:
            normalized_bias = 0.0

        # Detect confluence
        atlas_sig = next((s for s in signals if s.agent_name == "ATLAS"), None)
        orion_sig = next((s for s in signals if s.agent_name == "ORION"), None)

        atlas_polarity = self._polarity(atlas_sig.signal_type) if atlas_sig else 0.0
        orion_polarity = self._polarity(orion_sig.signal_type) if orion_sig else 0.0

        if atlas_polarity != 0 and orion_polarity != 0:
            if atlas_polarity == orion_polarity:
                confluence = "strong"
            else:
                confluence = "conflicting"
        elif atlas_polarity != 0 or orion_polarity != 0:
            confluence = "moderate"
        else:
            confluence = "weak"

        # Build fusion context for LLM
        fusion_context = {
            "weighted_bias": normalized_bias,
            "confluence": confluence,
            "agent_breakdown": agent_summary,
            "regime": regime_context.to_dict() if regime_context else None,
        }

        prompt = (
            f"Ativo: {asset}\n"
            f"Bias ponderado: {normalized_bias}\n"
            f"Confluencia ATLAS/ORION: {confluence}\n"
            f"Regime central: {regime_context.regime_id if regime_context else 'nao_informado'}\n"
            f"Breakdown por agente:\n"
        )
        for name, info in agent_summary.items():
            prompt += f"  {name}: {info['signal_type']} (conf={info['confidence']}, peso={info['weight']}, contrib={info['contribution']})\n"

        tf_for_legenda = normalize_chart_timeframe(chart_timeframe) if chart_timeframe else None
        legenda = timeframe_strategy_legenda(tf_for_legenda)
        prompt = f"[Contexto por timeframe — AEGIS]\n{legenda}\n\n{prompt}"

        response = self.llm.generate_response(self.system_prompt, prompt)
        data = extract_json_object(response)

        validate_required_keys(
            data,
            ["score", "classification", "direction", "explanation", "confluence_level"],
            "saida do AEGIS",
        )

        score = require_percentage(data["score"], "score")
        classification = normalize_classification(data["classification"])
        direction = normalize_direction(data["direction"])
        explanation = require_non_empty_string(data["explanation"], "explanation")
        confluence_level = normalize_confluence_level(data["confluence_level"])

        # Build StrategyDecision — timeframe do grafico (UI) sobrepoe faixa generica do modo
        mode_tf = self._timeframe(self.default_mode)
        strategy_tf = chart_timeframe.strip() if chart_timeframe else mode_tf
        strategy = StrategyDecision(
            mode=self.default_mode,
            direction=direction,
            timeframe=strategy_tf,
            confidence=min(99.0, max(0.0, score)),
            operational_status=self._operational_status(classification),
            reasons=reasons[:5],
            execution_hint=self._execution_hint(direction, strategy_tf, classification),
            regime_id=regime_context.regime_id if regime_context else None,
            regime_label=regime_context.regime_label if regime_context else None,
            regime_version=regime_context.regime_version if regime_context else None,
            regime_confidence=regime_context.regime_confidence if regime_context else None,
        )

        # Persist fusion features
        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="AEGIS",
                features={
                    "weighted_bias": normalized_bias,
                    "confluence": confluence_level,
                    "score": score,
                    "classification": classification,
                    "direction": direction,
                    "agent_contributions": agent_summary,
                    "agents_evaluated": [signal.agent_name for signal in signals],
                    "regime_id": regime_context.regime_id if regime_context else None,
                    "regime_version": regime_context.regime_version if regime_context else None,
                    "regime_confidence": regime_context.regime_confidence if regime_context else None,
                },
                metadata={
                    "regime_label": regime_context.regime_label if regime_context else None,
                },
            )

        alert = OpportunityAlert(
            asset=asset,
            score=score,
            classification=classification,
            explanation=explanation,
            sources=[s.agent_name for s in signals],
            strategy=strategy,
            chart_timeframe=chart_timeframe.strip() if chart_timeframe else None,
        )

        return alert

    def _operational_status(self, classification: str) -> str:
        if classification == "OPORTUNIDADE":
            return "monitorando_execucao"
        if classification == "RISCO":
            return "modo_defensivo"
        return "somente_observacao"

    def _execution_hint(self, direction: str, timeframe: str, classification: str) -> str:
        if direction == "flat":
            return "Aguardar nova confluencia antes de executar."
        if classification != "OPORTUNIDADE":
            return f"Execucao restrita; operar apenas com protecao reforcada no timeframe {timeframe}."
        return f"Priorizar entrada alinhada a {direction} no timeframe {timeframe}."
