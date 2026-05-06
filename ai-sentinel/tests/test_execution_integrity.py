import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.execution_integrity import ExecutionIntegrityError, ExecutionIntegrityGuard
from core.schemas import OpportunityAlert, SentinelGovernanceDecision, StrategyDecision


class _FakeFeatureStore:
    def __init__(self, feature_map):
        self.feature_map = feature_map

    def get_signal_feature_map(self, signal_id):
        return self.feature_map


class _FakeSentinelStore:
    def __init__(self, decision):
        self.decision = decision

    def get_decision_for_signal(self, signal_id):
        return self.decision


class ExecutionIntegrityTests(unittest.TestCase):
    def _build_alert(self):
        return OpportunityAlert(
            asset="BTCUSDT",
            score=88.0,
            classification="OPORTUNIDADE",
            explanation="Teste de integridade",
            sources=["AEGIS"],
            strategy=StrategyDecision(
                mode="swing",
                direction="LONG",
                timeframe="15m",
                confidence=88.0,
                operational_status="monitorando",
                reasons=["teste"],
                regime_id="trend_up",
                regime_label="Trend Up",
                regime_version="v1",
                regime_confidence=77.0,
            ),
            governance=SentinelGovernanceDecision(
                signal_id="sig-123",
                regime_id="trend_up",
                regime_version="v1",
                sentinel_decision="allow",
                sentinel_confidence=80.0,
                block_reason_code="none",
                expected_confidence_delta=0.0,
                approved=True,
                reason_codes=[],
                risk_flags=[],
            ),
        )

    def test_validate_dispatch_ready_accepts_consistent_alert(self):
        guard = ExecutionIntegrityGuard(
            feature_store=_FakeFeatureStore(
                {
                    "REGIME_ENGINE": {"features": {"regime_id": "trend_up", "regime_version": "v1"}},
                    "AEGIS": {"features": {"score": 88.0}},
                    "SENTINEL": {"features": {"approved": True}},
                }
            ),
            sentinel_store=_FakeSentinelStore(
                {
                    "signal_id": "sig-123",
                    "regime_id": "trend_up",
                    "regime_version": "v1",
                    "sentinel_decision": "allow",
                }
            ),
        )

        result = guard.validate_dispatch_ready(self._build_alert())
        self.assertEqual(result["signal_id"], "sig-123")
        self.assertEqual(result["regime_id"], "trend_up")

    def test_validate_dispatch_ready_fails_without_sentinel_persistence(self):
        guard = ExecutionIntegrityGuard(
            feature_store=_FakeFeatureStore(
                {
                    "REGIME_ENGINE": {"features": {"regime_id": "trend_up", "regime_version": "v1"}},
                    "AEGIS": {"features": {"score": 88.0}},
                    "SENTINEL": {"features": {"approved": True}},
                }
            ),
            sentinel_store=_FakeSentinelStore(None),
        )

        with self.assertRaises(ExecutionIntegrityError):
            guard.validate_dispatch_ready(self._build_alert())

    def test_validate_dispatch_ready_fails_when_required_feature_is_missing(self):
        guard = ExecutionIntegrityGuard(
            feature_store=_FakeFeatureStore(
                {
                    "REGIME_ENGINE": {"features": {"regime_id": "trend_up", "regime_version": "v1"}},
                    "AEGIS": {"features": {"score": 88.0}},
                }
            ),
            sentinel_store=_FakeSentinelStore(
                {
                    "signal_id": "sig-123",
                    "regime_id": "trend_up",
                    "regime_version": "v1",
                    "sentinel_decision": "allow",
                }
            ),
        )

        with self.assertRaises(ExecutionIntegrityError):
            guard.validate_dispatch_ready(self._build_alert())


if __name__ == "__main__":
    unittest.main()