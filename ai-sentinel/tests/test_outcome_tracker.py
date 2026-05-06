import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.outcome_tracker import OutcomeTracker


class OutcomeTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        os.environ["OUTCOME_LOG_PATH"] = self.tmp.name
        os.environ.pop("NEXT_PUBLIC_SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)
        self.tracker = OutcomeTracker()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def test_record_outcome_creates_entry(self):
        result = self.tracker.record_outcome(
            signal_id="sig-001",
            asset="BTCUSDT",
            direction="long",
            entry_price=60000.0,
            exit_price=61200.0,
            pnl_percent=2.0,
            result="win",
            timeframe="4h-1d",
            strategy="swing",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["signal_id"], "sig-001")
        self.assertFalse(result["supabase"]["persisted"])

        with open(self.tmp.name, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["result"], "win")
        self.assertEqual(payload["pnl_percent"], 2.0)

    def test_invalid_result_raises(self):
        with self.assertRaises(ValueError):
            self.tracker.record_outcome(
                signal_id="sig-bad",
                asset="ETHUSDT",
                direction="short",
                entry_price=3000.0,
                exit_price=3100.0,
                pnl_percent=-3.3,
                result="unknown_status",
            )

    def test_get_recent_outcomes_filters(self):
        for i, (asset, res) in enumerate([
            ("BTCUSDT", "win"),
            ("ETHUSDT", "loss"),
            ("BTCUSDT", "loss"),
            ("SOLUSDT", "win"),
        ]):
            self.tracker.record_outcome(
                signal_id=f"sig-{i}",
                asset=asset,
                direction="long",
                entry_price=100.0,
                exit_price=101.0 if res == "win" else 99.0,
                pnl_percent=1.0 if res == "win" else -1.0,
                result=res,
            )

        all_items = self.tracker.get_recent_outcomes(limit=100)
        self.assertEqual(all_items["count"], 4)

        btc_only = self.tracker.get_recent_outcomes(limit=100, asset="BTCUSDT")
        self.assertEqual(btc_only["count"], 2)

    def test_compute_performance_metrics(self):
        outcomes = [
            ("BTCUSDT", "long", 60000, 61200, 2.0, "win"),
            ("BTCUSDT", "long", 61200, 60588, -1.0, "loss"),
            ("BTCUSDT", "short", 60000, 59400, 1.0, "win"),
            ("ETHUSDT", "long", 3000, 3150, 5.0, "win"),
            ("ETHUSDT", "long", 3150, 3087, -2.0, "loss"),
        ]
        for i, (asset, direction, entry, exit_, pnl, result) in enumerate(outcomes):
            self.tracker.record_outcome(
                signal_id=f"perf-{i}",
                asset=asset,
                direction=direction,
                entry_price=entry,
                exit_price=exit_,
                pnl_percent=pnl,
                result=result,
                strategy="swing",
                timeframe="4h-1d",
            )

        perf = self.tracker.compute_performance(window_days=1)
        self.assertTrue(perf["success"])
        self.assertEqual(perf["totals"]["trades"], 5)
        self.assertEqual(perf["totals"]["wins"], 3)
        self.assertEqual(perf["totals"]["losses"], 2)
        self.assertEqual(perf["metrics"]["win_rate"], 60.0)
        self.assertGreater(perf["metrics"]["profit_factor"], 1.0)
        self.assertGreater(perf["metrics"]["expectancy_pct"], 0.0)
        self.assertIn("BTCUSDT", perf["by_asset"])
        self.assertIn("ETHUSDT", perf["by_asset"])

        btc_perf = self.tracker.compute_performance(window_days=1, asset="BTCUSDT")
        self.assertEqual(btc_perf["totals"]["trades"], 3)

    def test_compute_performance_empty(self):
        perf = self.tracker.compute_performance(window_days=1)
        self.assertTrue(perf["success"])
        self.assertEqual(perf["totals"]["trades"], 0)
        self.assertEqual(perf["metrics"]["win_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
