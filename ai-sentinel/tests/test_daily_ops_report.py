import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.daily_ops_report import DailyOpsReportService


class DailyOpsReportTests(unittest.TestCase):
    def _iso_today(self):
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def test_generates_daily_metrics_from_dispatch_log(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as fp:
            fp.write(json.dumps({
                "timestamp": self._iso_today(),
                "asset": "BTCUSDT",
                "status": "blocked",
                "error": "fora_do_filtro",
                "scanner_result": {"reason": "fora_do_filtro", "desk_action": "ignored"},
            }) + "\n")
            fp.write(json.dumps({
                "timestamp": self._iso_today(),
                "asset": "BTCUSDT",
                "status": "sent",
                "scanner_result": {"desk_action": "executed"},
            }) + "\n")
            fp.write(json.dumps({
                "timestamp": self._iso_today(),
                "asset": "ETHUSDT",
                "status": "failed",
                "error": "sistema_halted",
                "scanner_result": {"reason": "sistema_halted", "desk_action": "blocked"},
            }) + "\n")
            log_path = fp.name

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as risk_fp:
            risk_fp.write(json.dumps({
                "event": "kill_switch_triggered",
                "timestamp": self._iso_today(),
                "reasons": ["daily_loss_limit_reached"],
            }) + "\n")
            risk_log_path = risk_fp.name

        try:
            with patch.dict(
                os.environ,
                {
                    "SIGNAL_DISPATCH_LOG_PATH": log_path,
                    "KILL_SWITCH_LOG_PATH": risk_log_path,
                },
                clear=False,
            ):
                service = DailyOpsReportService()
                report = service.generate_daily_report()

            self.assertTrue(report["success"])
            self.assertEqual(report["totals"]["signals_generated"], 3)
            self.assertEqual(report["totals"]["signals_blocked"], 1)
            self.assertEqual(report["totals"]["signals_failed"], 1)
            self.assertEqual(report["totals"]["executed"], 1)
            self.assertEqual(report["totals"]["risk_events"], 1)
            self.assertTrue(report["top_reasons_block"])
        finally:
            try:
                os.unlink(log_path)
            except Exception:
                pass
            try:
                os.unlink(risk_log_path)
            except Exception:
                pass

    def test_raises_when_dispatch_log_missing(self):
        missing = str((ROOT_DIR / "runtime_logs" / "_file_missing_for_test.jsonl").resolve())
        with patch.dict(os.environ, {"SIGNAL_DISPATCH_LOG_PATH": missing}, clear=False):
            service = DailyOpsReportService()
            with self.assertRaises(RuntimeError):
                service.generate_daily_report()


if __name__ == "__main__":
    unittest.main()
