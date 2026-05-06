import os
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.feature_store import FeatureStore
from core.outcome_tracker import OutcomeTracker


class FeatureStoreSupervisedTests(unittest.TestCase):
    def setUp(self):
        self.feature_tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.feature_tmp.close()
        self.outcome_tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.outcome_tmp.close()

        os.environ["FEATURE_STORE_LOG_PATH"] = self.feature_tmp.name
        os.environ["OUTCOME_LOG_PATH"] = self.outcome_tmp.name
        os.environ.pop("NEXT_PUBLIC_SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)

        self.feature_store = FeatureStore()
        self.outcome_tracker = OutcomeTracker()

    def tearDown(self):
        for path in (self.feature_tmp.name, self.outcome_tmp.name):
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_supervised_export_joins_features_and_outcomes(self):
        self.feature_store.persist(
            signal_id="sig-001",
            asset="BTCUSDT",
            agent_name="ATLAS",
            features={
                "rsi_14_1d": 55.0,
                "structure": {"bos": True, "score": 72.5},
                "emitted_confidence": 81.0,
            },
            metadata={"signal_type": "STRONG BUY"},
        )
        self.outcome_tracker.record_outcome(
            signal_id="sig-001",
            asset="BTCUSDT",
            direction="long",
            entry_price=100.0,
            exit_price=104.0,
            pnl_percent=4.0,
            result="win",
            strategy="swing",
        )

        exported = self.feature_store.export_supervised_dataset(
            outcome_tracker=self.outcome_tracker,
            asset="BTCUSDT",
            limit=100,
        )

        self.assertTrue(exported["success"])
        self.assertEqual(exported["count"], 1)
        item = exported["items"][0]
        self.assertEqual(item["signal_id"], "sig-001")
        self.assertEqual(item["outcome"]["result"], "win")
        self.assertEqual(item["numeric_features"]["rsi_14_1d"], 55.0)
        self.assertEqual(item["numeric_features"]["structure.bos"], 1.0)
        self.assertEqual(item["numeric_features"]["structure.score"], 72.5)

    def test_weight_recommendations_use_real_outcomes(self):
        for index, pnl in enumerate([3.0, 2.0, 1.0, 2.5, 1.5], start=1):
            signal_id = f"atlas-{index}"
            self.feature_store.persist(
                signal_id=signal_id,
                asset="BTCUSDT",
                agent_name="ATLAS",
                features={"emitted_confidence": 80.0 + index, "feature_a": float(index)},
                metadata={"signal_type": "STRONG BUY"},
            )
            self.outcome_tracker.record_outcome(
                signal_id=signal_id,
                asset="BTCUSDT",
                direction="long",
                entry_price=100.0,
                exit_price=100.0 + pnl,
                pnl_percent=pnl,
                result="win",
                strategy="swing",
            )

        for index, pnl in enumerate([-2.0, -1.0, -1.5, -0.5, -2.5], start=1):
            signal_id = f"sentiment-{index}"
            self.feature_store.persist(
                signal_id=signal_id,
                asset="BTCUSDT",
                agent_name="SentimentAgent",
                features={"emitted_confidence": 60.0 + index, "feature_b": float(index)},
                metadata={"signal_type": "NEGATIVE"},
            )
            self.outcome_tracker.record_outcome(
                signal_id=signal_id,
                asset="BTCUSDT",
                direction="long",
                entry_price=100.0,
                exit_price=100.0 + pnl,
                pnl_percent=pnl,
                result="loss",
                strategy="swing",
            )

        preview = self.feature_store.compute_agent_weight_recommendations(
            outcome_tracker=self.outcome_tracker,
            asset="BTCUSDT",
            window_days=365,
            min_samples=5,
        )

        self.assertTrue(preview["success"])
        self.assertIn("ATLAS", preview["agents"])
        self.assertIn("SentimentAgent", preview["agents"])
        self.assertGreater(preview["agents"]["ATLAS"]["avg_pnl_pct"], 0)
        self.assertLess(preview["agents"]["SentimentAgent"]["avg_pnl_pct"], 0)
        self.assertIn("ATLAS", preview["weights"])
        self.assertNotIn("SentimentAgent", preview["weights"])

    def test_supervised_export_can_filter_by_regime(self):
        self.feature_store.persist(
            signal_id="sig-regime-1",
            asset="BTCUSDT",
            agent_name="REGIME_ENGINE",
            features={
                "regime_id": "trend_risk_on",
                "regime_label": "Tendencia com apetite a risco",
                "regime_version": "regime_engine.v1",
                "regime_confidence": 83.0,
            },
        )
        self.feature_store.persist(
            signal_id="sig-regime-1",
            asset="BTCUSDT",
            agent_name="ATLAS",
            features={"emitted_confidence": 82.0, "feature_a": 1.0},
        )
        self.outcome_tracker.record_outcome(
            signal_id="sig-regime-1",
            asset="BTCUSDT",
            direction="long",
            entry_price=100.0,
            exit_price=103.0,
            pnl_percent=3.0,
            result="win",
            strategy="swing",
        )

        self.feature_store.persist(
            signal_id="sig-regime-2",
            asset="BTCUSDT",
            agent_name="REGIME_ENGINE",
            features={
                "regime_id": "range_bound",
                "regime_label": "Range / lateralidade",
                "regime_version": "regime_engine.v1",
                "regime_confidence": 61.0,
            },
        )
        self.feature_store.persist(
            signal_id="sig-regime-2",
            asset="BTCUSDT",
            agent_name="ATLAS",
            features={"emitted_confidence": 65.0, "feature_a": 2.0},
        )
        self.outcome_tracker.record_outcome(
            signal_id="sig-regime-2",
            asset="BTCUSDT",
            direction="long",
            entry_price=100.0,
            exit_price=99.0,
            pnl_percent=-1.0,
            result="loss",
            strategy="swing",
        )

        exported = self.feature_store.export_supervised_dataset(
            outcome_tracker=self.outcome_tracker,
            asset="BTCUSDT",
            agent_name="ATLAS",
            regime_id="trend_risk_on",
            regime_version="regime_engine.v1",
            limit=100,
        )

        self.assertEqual(exported["count"], 1)
        self.assertEqual(exported["items"][0]["regime"]["regime_id"], "trend_risk_on")


if __name__ == "__main__":
    unittest.main()