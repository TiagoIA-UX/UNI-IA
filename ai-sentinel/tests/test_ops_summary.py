import os
import sys
import tempfile
import unittest
import importlib
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class OpsSummaryTests(unittest.TestCase):
    def test_ops_summary_returns_combined_payload(self):
        dispatch_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8")
        risk_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8")
        dispatch_file.write("{}\n")
        risk_file.write("{}\n")
        dispatch_file.close()
        risk_file.close()

        try:
            with patch.dict(
                os.environ,
                {
                    "UNI_IA_ADMIN_TOKEN": "test-token",
                    "AUDIT_TABLE_NAME": "uni_ia_events",
                    "AUDIT_EVENT_VARIANT": "A",
                    "UNI_IA_ALLOWED_ORIGINS": "http://localhost:3000",
                    "UNI_IA_MODE": "paper",
                    "COPY_TRADE_ENABLED": "false",
                    "SIGNAL_DISPATCH_LOG_PATH": dispatch_file.name,
                    "KILL_SWITCH_LOG_PATH": risk_file.name,
                    "NEXT_PUBLIC_SUPABASE_URL": "",
                    "SUPABASE_SERVICE_ROLE_KEY": "",
                },
                clear=False,
            ):
                import api.main as main_api
                main_api = importlib.reload(main_api)
                reports_ops_summary = main_api.reports_ops_summary

                response = reports_ops_summary(
                    date=None,
                    risk_events_limit=5,
                    dispatch_window_minutes=1440,
                    dispatch_sample_limit=5000,
                    _=None,
                )

            self.assertTrue(response["success"])
            data = response["data"]
            self.assertIn("daily_report", data)
            self.assertIn("risk_status", data)
            self.assertIn("risk_recent_events", data)
            self.assertIn("dispatch_metrics", data)
            self.assertIn("system", data)
            self.assertIn("desk", data)
            self.assertIn("copy_trade", data)
            self.assertIn("scanner", data)
            self.assertIn("strict_readiness", data)
            self.assertIn("checks", data)
            self.assertIn("failed_checks", data)
            self.assertIn("reasons", data)
            self.assertIn("reason_details", data)
            self.assertIn("overall_severity", data)
            self.assertIn("readiness", data)
            self.assertIn("checks", data["readiness"])
            self.assertIn("reason_details", data["readiness"])
            self.assertIn("overall_severity", data["readiness"])
        finally:
            try:
                os.unlink(dispatch_file.name)
            except Exception:
                pass
            try:
                os.unlink(risk_file.name)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
