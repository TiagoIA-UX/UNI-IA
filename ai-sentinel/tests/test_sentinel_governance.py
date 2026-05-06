import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from agents.sentinel_agent import SentinelAgent
from core.outcome_tracker import OutcomeTracker
from core.regime_engine import RegimeContext
from core.schemas import OpportunityAlert, StrategyDecision
from core.sentinel_decision_store import SentinelDecisionStore


class SentinelGovernanceTests(unittest.TestCase):
    def setUp(self):
        self.sentinel_tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.sentinel_tmp.close()
        self.outcome_tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.outcome_tmp.close()
        self.feature_tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.feature_tmp.close()

        os.environ["SENTINEL_DECISION_LOG_PATH"] = self.sentinel_tmp.name
        os.environ["OUTCOME_LOG_PATH"] = self.outcome_tmp.name
        os.environ["FEATURE_STORE_LOG_PATH"] = self.feature_tmp.name
        os.environ.pop("NEXT_PUBLIC_SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)

        self.store = SentinelDecisionStore()
        self.outcome_tracker = OutcomeTracker()
        self.sentinel = SentinelAgent(
            sentinel_store=self.store,
            outcome_tracker=self.outcome_tracker,
        )
        self.regime_context = RegimeContext(
            regime_id="trend_risk_on",
            regime_label="Tendencia com apetite a risco",
            regime_version="regime_engine.v1",
            regime_confidence=82.0,
            volatility_regime="normal",
            market_structure="bullish",
            liquidity_regime="normal",
            macro_regime="RISK-ON",
            news_regime="RISK-ON",
            event_pressure="low",
            regime_features={},
        )

    def tearDown(self):
        for path in (self.sentinel_tmp.name, self.outcome_tmp.name, self.feature_tmp.name):
            try:
                os.unlink(path)
            except Exception:
                pass

    def _build_alert(self, *, score: float, classification: str = "OPORTUNIDADE") -> OpportunityAlert:
        return OpportunityAlert(
            asset="BTCUSDT",
            score=score,
            classification=classification,
            explanation="alerta de teste",
            sources=["ATLAS", "ORION"],
            strategy=StrategyDecision(
                mode="swing",
                direction="long",
                timeframe="4h-1d",
                confidence=score,
                operational_status="ready",
                reasons=["setup_valido"],
                regime_id=self.regime_context.regime_id,
                regime_label=self.regime_context.regime_label,
                regime_version=self.regime_context.regime_version,
                regime_confidence=self.regime_context.regime_confidence,
            ),
        )

    def test_sentinel_persists_structured_decision(self):
        result = self.sentinel.evaluate(
            self._build_alert(score=50.0),
            signal_id="sig-001",
            regime_context=self.regime_context,
        )

        self.assertFalse(result["approved"])
        self.assertEqual(result["sentinel_decision"], "block")
        self.assertEqual(result["block_reason_code"], "score_below_dispatch_min")
        self.assertLess(result["expected_confidence_delta"], 0.0)

        rows = self.store.export_decisions(limit=10)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["signal_id"], "sig-001")
        self.assertEqual(rows[0]["regime_id"], "trend_risk_on")
        self.assertEqual(rows[0]["sentinel_decision"], "block")

        with open(self.sentinel_tmp.name, "r", encoding="utf-8") as fp:
            payload = json.loads(fp.readline())
        self.assertEqual(payload["block_reason_code"], "score_below_dispatch_min")
        self.assertEqual(payload["approved"], False)

    def test_regime_metrics_measure_alpha_lost_and_drawdown_avoided(self):
        self.store.record_decision(
            signal_id="sig-win-blocked",
            asset="BTCUSDT",
            regime_id="trend_risk_on",
            regime_version="regime_engine.v1",
            sentinel_decision="block",
            sentinel_confidence=90.0,
            block_reason_code="score_below_dispatch_min",
            expected_confidence_delta=-60.0,
            approved=False,
            reason_codes=["score_below_dispatch_min"],
            risk_flags=[],
            score=60.0,
            classification="ATENCAO",
            direction="long",
            timeframe="4h-1d",
            strategy_confidence=60.0,
        )
        self.outcome_tracker.record_outcome(
            signal_id="sig-win-blocked",
            asset="BTCUSDT",
            direction="long",
            entry_price=100.0,
            exit_price=102.5,
            pnl_percent=2.5,
            result="win",
            strategy="swing",
        )

        self.store.record_decision(
            signal_id="sig-loss-blocked",
            asset="BTCUSDT",
            regime_id="trend_risk_on",
            regime_version="regime_engine.v1",
            sentinel_decision="block",
            sentinel_confidence=88.0,
            block_reason_code="max_drawdown_limit",
            expected_confidence_delta=-82.0,
            approved=False,
            reason_codes=["max_drawdown_limit"],
            risk_flags=[],
            score=82.0,
            classification="OPORTUNIDADE",
            direction="long",
            timeframe="4h-1d",
            strategy_confidence=82.0,
        )
        self.outcome_tracker.record_outcome(
            signal_id="sig-loss-blocked",
            asset="BTCUSDT",
            direction="long",
            entry_price=100.0,
            exit_price=97.0,
            pnl_percent=-3.0,
            result="loss",
            strategy="swing",
        )

        self.store.record_decision(
            signal_id="sig-allow",
            asset="BTCUSDT",
            regime_id="trend_risk_on",
            regime_version="regime_engine.v1",
            sentinel_decision="allow",
            sentinel_confidence=65.0,
            block_reason_code="none",
            expected_confidence_delta=0.0,
            approved=True,
            reason_codes=[],
            risk_flags=[],
            score=86.0,
            classification="OPORTUNIDADE",
            direction="long",
            timeframe="4h-1d",
            strategy_confidence=86.0,
        )

        metrics = self.store.compute_regime_metrics(
            outcome_tracker=self.outcome_tracker,
            asset="BTCUSDT",
            window_days=365,
        )

        self.assertTrue(metrics["success"])
        self.assertEqual(len(metrics["regimes"]), 1)
        regime_metrics = metrics["regimes"][0]
        self.assertEqual(regime_metrics["blocked_count"], 2)
        self.assertEqual(regime_metrics["false_block_count"], 1)
        self.assertEqual(regime_metrics["drawdown_avoided_count"], 1)
        self.assertEqual(regime_metrics["alpha_lost_total_pct"], 2.5)
        self.assertEqual(regime_metrics["drawdown_avoided_total_pct"], 3.0)
        self.assertEqual(regime_metrics["governance_value_pct"], 0.5)


if __name__ == "__main__":
    unittest.main()