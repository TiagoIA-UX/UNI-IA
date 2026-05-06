"""SENTINEL — Agente de Governanca e Risco.

SENTINEL decide: "Mesmo sendo bom, pode executar?"

Funcao:
  - Risk filter pre-execucao
  - Validacao de regime (kill switch)
  - Validacao de desk mode
  - Bloqueio por drawdown / loss streak
  - Registra decisao de governanca no FeatureStore

SENTINEL e a camada entre AEGIS e o Dispatch.
Nada passa sem a aprovacao do SENTINEL.
"""

from typing import Any, Dict, List, Optional

from core.contract_validation import normalize_classification, validate_opportunity_alert
from core.feature_store import FeatureStore
from core.outcome_tracker import OutcomeTracker
from core.regime_engine import RegimeContext
from core.schemas import OpportunityAlert
from core.sentinel_decision_store import SentinelDecisionStore
from core.system_state import SystemStateManager, SystemStatus


class SentinelAgent:
    """Agente de Governanca e Risco — SENTINEL."""

    def __init__(
        self,
        system_state: Optional[SystemStateManager] = None,
        feature_store: Optional[FeatureStore] = None,
        outcome_tracker: Optional[OutcomeTracker] = None,
        sentinel_store: Optional[SentinelDecisionStore] = None,
        *,
        max_drawdown_pct: float = 15.0,
        max_consecutive_losses: int = 4,
        min_score_to_dispatch: float = 70.0,
    ):
        self.system_state = system_state
        self.feature_store = feature_store or FeatureStore()
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.sentinel_store = sentinel_store or SentinelDecisionStore()
        self.max_drawdown_pct = max_drawdown_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.min_score_to_dispatch = min_score_to_dispatch

    def _primary_reason_code(self, reason_codes: List[str], risk_flags: List[str]) -> str:
        if reason_codes:
            return reason_codes[0]
        if risk_flags:
            return risk_flags[0]
        return "none"

    def _expected_confidence_delta(self, *, decision: str, alert_score: float) -> float:
        if decision == "block":
            return round(-float(alert_score), 6)
        if decision == "downgrade":
            target_score = max(0.0, min(float(alert_score) - 10.0, self.min_score_to_dispatch - 1.0))
            return round(target_score - float(alert_score), 6)
        return 0.0

    def _sentinel_confidence(self, *, decision: str, reason_codes: List[str], risk_flags: List[str]) -> float:
        confidence = 55.0 + (len(reason_codes) * 12.0) + (len(risk_flags) * 6.0)
        if decision == "block":
            confidence += 15.0
        elif decision == "downgrade":
            confidence += 5.0
        return max(0.0, min(99.0, round(confidence, 4)))

    # ------------------------------------------------------------------
    # Gate
    # ------------------------------------------------------------------

    def evaluate(
        self,
        alert: OpportunityAlert,
        signal_id: Optional[str] = None,
        regime_context: Optional[RegimeContext] = None,
    ) -> Dict[str, Any]:
        """Avalia se o alerta pode prosseguir para dispatch/execucao.

        Returns:
            {
                "approved": bool,
                "action": "pass" | "block" | "reduce",
                "reasons": [...],
                "risk_flags": [...],
            }
        """
        reason_codes: List[str] = []
        risk_flags: List[str] = []
        decision = "allow"
        validate_opportunity_alert(alert)

        # 1. System state check
        if self.system_state:
            status = self.system_state.status
            if status in (SystemStatus.HALTED, SystemStatus.LOCKED):
                reason_codes.append(f"system_status_{status.value}")
                decision = "block"
            elif status == SystemStatus.DEGRADED:
                risk_flags.append("system_degraded")

        # 2. Score minimum
        if float(alert.score) < self.min_score_to_dispatch:
            reason_codes.append("score_below_dispatch_min")
            decision = "block"

        # 3. Classification check
        if normalize_classification(alert.classification) == "RISCO":
            risk_flags.append("classificacao_risco")
            if decision != "block":
                decision = "downgrade"

        # 4. Performance-based risk check
        try:
            perf = self.outcome_tracker.compute_performance(window_days=7)
            if perf.get("success") and perf["totals"]["trades"] >= 5:
                # Drawdown guard
                if perf["metrics"]["max_drawdown_pct"] >= self.max_drawdown_pct:
                    reason_codes.append("max_drawdown_limit")
                    decision = "block"

                # Win rate degradation
                if perf["metrics"]["win_rate"] < 35.0:
                    risk_flags.append("critical_win_rate")
                    if decision == "allow":
                        decision = "downgrade"

                # Loss streak (approximate)
                recent = self.outcome_tracker.get_recent_outcomes(limit=self.max_consecutive_losses)
                if recent.get("count", 0) >= self.max_consecutive_losses:
                    all_losses = all(
                        item.get("result") == "loss"
                        for item in recent.get("items", [])[:self.max_consecutive_losses]
                    )
                    if all_losses:
                        reason_codes.append("loss_streak_limit")
                        decision = "block"
        except Exception as exc:
            reason_codes.append("outcome_tracker_unavailable")
            risk_flags.append(f"tracker_error:{type(exc).__name__}")
            decision = "block"

        # 5. Direction sanity
        if alert.strategy and alert.strategy.direction == "flat":
            risk_flags.append("direction_flat")

        approved = decision != "block"
        block_reason_code = self._primary_reason_code(reason_codes, risk_flags)
        sentinel_confidence = self._sentinel_confidence(
            decision=decision,
            reason_codes=reason_codes,
            risk_flags=risk_flags,
        )
        expected_confidence_delta = self._expected_confidence_delta(
            decision=decision,
            alert_score=float(alert.score),
        )
        action = "pass" if decision == "allow" else "block" if decision == "block" else "reduce"
        regime_id = (
            regime_context.regime_id if regime_context else getattr(getattr(alert, "strategy", None), "regime_id", None)
        ) or "unknown"
        regime_version = (
            regime_context.regime_version if regime_context else getattr(getattr(alert, "strategy", None), "regime_version", None)
        ) or "unknown"
        regime_confidence = (
            regime_context.regime_confidence if regime_context else getattr(getattr(alert, "strategy", None), "regime_confidence", None)
        )

        result = {
            "approved": approved,
            "action": action,
            "reasons": reason_codes,
            "risk_flags": risk_flags,
            "sentinel_decision": decision,
            "sentinel_confidence": sentinel_confidence,
            "block_reason_code": block_reason_code,
            "expected_confidence_delta": expected_confidence_delta,
            "reason_codes": reason_codes,
            "regime_id": regime_id,
            "regime_version": regime_version,
        }

        # Persist governance decision
        if signal_id:
            payload = {
                "signal_id": signal_id,
                "asset": alert.asset,
                "regime_id": regime_id,
                "regime_version": regime_version,
                "regime_confidence": regime_confidence,
                "sentinel_decision": decision,
                "sentinel_confidence": sentinel_confidence,
                "block_reason_code": block_reason_code,
                "expected_confidence_delta": expected_confidence_delta,
                "approved": approved,
                "reason_codes": reason_codes,
                "risk_flags": risk_flags,
                "score": float(alert.score),
                "classification": alert.classification,
                "direction": alert.strategy.direction if alert.strategy else None,
                "timeframe": alert.strategy.timeframe if alert.strategy else None,
                "strategy_confidence": alert.strategy.confidence if alert.strategy else None,
                "metadata": {
                    "operational_status": alert.strategy.operational_status if alert.strategy else None,
                },
            }
            self.sentinel_store.record_decision(**payload)
            self.feature_store.persist(
                signal_id=signal_id,
                asset=alert.asset,
                agent_name="SENTINEL",
                features={
                    "approved": approved,
                    "action": action,
                    "sentinel_decision": decision,
                    "sentinel_confidence": sentinel_confidence,
                    "block_reason_code": block_reason_code,
                    "expected_confidence_delta": expected_confidence_delta,
                    "regime_id": regime_id,
                    "regime_version": regime_version,
                    "score": float(alert.score),
                    "classification": alert.classification,
                    "reasons": reason_codes,
                    "risk_flags": risk_flags,
                },
                metadata={
                    "signal_id": signal_id,
                },
            )

        return result
