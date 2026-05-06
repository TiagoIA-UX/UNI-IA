from typing import Any, Dict

from core.schemas import OpportunityAlert


class ExecutionIntegrityError(RuntimeError):
    pass


class ExecutionIntegrityGuard:
    """Valida integridade minima antes de dispatch e execucao."""

    def __init__(self, *, feature_store, sentinel_store):
        self.feature_store = feature_store
        self.sentinel_store = sentinel_store

    def validate_dispatch_ready(self, alert: OpportunityAlert) -> Dict[str, Any]:
        governance = getattr(alert, "governance", None)
        strategy = getattr(alert, "strategy", None)

        if governance is None:
            raise ExecutionIntegrityError("execution_integrity: governanca do SENTINEL ausente no alerta.")
        if strategy is None:
            raise ExecutionIntegrityError("execution_integrity: strategy ausente no alerta consolidado.")

        signal_id = str(getattr(governance, "signal_id", "") or "").strip()
        regime_id = str(getattr(governance, "regime_id", "") or "").strip()
        regime_version = str(getattr(governance, "regime_version", "") or "").strip()

        if not signal_id:
            raise ExecutionIntegrityError("execution_integrity: signal_id ausente na governanca do alerta.")
        if not regime_id or not regime_version:
            raise ExecutionIntegrityError("execution_integrity: regime_id/regime_version ausentes na governanca.")

        if str(getattr(strategy, "regime_id", "") or "").strip() != regime_id:
            raise ExecutionIntegrityError("execution_integrity: strategy.regime_id divergente da governanca.")
        if str(getattr(strategy, "regime_version", "") or "").strip() != regime_version:
            raise ExecutionIntegrityError("execution_integrity: strategy.regime_version divergente da governanca.")

        feature_map = self.feature_store.get_signal_feature_map(signal_id)
        required_feature_agents = {"REGIME_ENGINE", "AEGIS", "SENTINEL"}
        missing_agents = sorted(agent for agent in required_feature_agents if agent not in feature_map)
        if missing_agents:
            raise ExecutionIntegrityError(
                "execution_integrity: features obrigatorias ausentes para signal_id "
                f"{signal_id}: {', '.join(missing_agents)}"
            )

        regime_entry = feature_map["REGIME_ENGINE"]
        regime_features = regime_entry.get("features", {}) if isinstance(regime_entry, dict) else {}
        if str(regime_features.get("regime_id", "") or "").strip() != regime_id:
            raise ExecutionIntegrityError("execution_integrity: REGIME_ENGINE.regime_id divergente da governanca.")
        if str(regime_features.get("regime_version", "") or "").strip() != regime_version:
            raise ExecutionIntegrityError("execution_integrity: REGIME_ENGINE.regime_version divergente da governanca.")

        sentinel_decision = self.sentinel_store.get_decision_for_signal(signal_id)
        if not sentinel_decision:
            raise ExecutionIntegrityError("execution_integrity: decisao do SENTINEL nao persistida para o signal_id.")
        if str(sentinel_decision.get("signal_id", "") or "").strip() != signal_id:
            raise ExecutionIntegrityError("execution_integrity: sentinel_store.signal_id divergente da governanca.")
        if str(sentinel_decision.get("regime_id", "") or "").strip() != regime_id:
            raise ExecutionIntegrityError("execution_integrity: sentinel_store.regime_id divergente da governanca.")
        if str(sentinel_decision.get("regime_version", "") or "").strip() != regime_version:
            raise ExecutionIntegrityError("execution_integrity: sentinel_store.regime_version divergente da governanca.")

        return {
            "signal_id": signal_id,
            "regime_id": regime_id,
            "regime_version": regime_version,
            "feature_agents": sorted(feature_map.keys()),
            "sentinel_decision": sentinel_decision.get("sentinel_decision"),
        }