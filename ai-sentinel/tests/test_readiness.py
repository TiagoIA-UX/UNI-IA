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


class ReadinessTests(unittest.TestCase):
    def test_readiness_endpoint_returns_check_matrix(self):
        dispatch_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        risk_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
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
                    "TELEGRAM_CONTROL_ENABLED": "true",
                    "TELEGRAM_ADMIN_CHAT_IDS": "",
                    "TELEGRAM_ADMIN_USER_IDS": "",
                    "SIGNAL_DISPATCH_LOG_PATH": dispatch_file.name,
                    "KILL_SWITCH_LOG_PATH": risk_file.name,
                    "NEXT_PUBLIC_SUPABASE_URL": "",
                    "SUPABASE_SERVICE_ROLE_KEY": "",
                },
                clear=False,
            ):
                import api.main as main_api
                main_api = importlib.reload(main_api)
                health_readiness = main_api.health_readiness

                response = health_readiness(None)

            self.assertTrue(response["success"])
            data = response["data"]
            self.assertIn("ready", data)
            self.assertIn("checks", data)
            self.assertIn("failed_checks", data)
            self.assertIn("reasons", data)
            self.assertIn("reason_details", data)
            self.assertIn("overall_severity", data)
            self.assertIn("system", data)
            self.assertIn("scanner", data)
            self.assertIn("telegram", data)
            self.assertIn("copy_trade", data)
            self.assertIn("risk", data)
            self.assertIn("audit", data)
            self.assertIn("audit_ready", data["checks"])
            self.assertIn("telegram_ready", data["checks"])
            self.assertIn("telegram_dispatch_ready", data["checks"])
            self.assertIn("telegram_ready", data["failed_checks"])
            self.assertIn("telegram_control_not_ready", data["reasons"])
            self.assertIn(
                {
                    "check": "telegram_ready",
                    "reason": "telegram_control_not_ready",
                    "severity": "warning",
                },
                data["reason_details"],
            )
            self.assertIn("dispatch_configured", data["telegram"])
            self.assertIn("desk_store_ready", data["failed_checks"])
            self.assertIn("desk_store_not_ready", data["reasons"])
            self.assertEqual(data["overall_severity"], "critical")
        finally:
            try:
                os.unlink(dispatch_file.name)
            except Exception:
                pass
            try:
                os.unlink(risk_file.name)
            except Exception:
                pass

    def test_readiness_marks_audit_not_ready_when_table_name_is_missing(self):
        dispatch_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        risk_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        dispatch_file.close()
        risk_file.close()

        try:
            with patch.dict(
                os.environ,
                {
                    "UNI_IA_ADMIN_TOKEN": "test-token",
                    "AUDIT_TABLE_NAME": "",
                    "UNI_IA_ALLOWED_ORIGINS": "http://localhost:3000",
                    "UNI_IA_MODE": "paper",
                    "COPY_TRADE_ENABLED": "false",
                    "TELEGRAM_CONTROL_ENABLED": "false",
                    "SIGNAL_DISPATCH_LOG_PATH": dispatch_file.name,
                    "KILL_SWITCH_LOG_PATH": risk_file.name,
                    "NEXT_PUBLIC_SUPABASE_URL": "https://example.supabase.co",
                    "SUPABASE_SERVICE_ROLE_KEY": "service-role-key",
                },
                clear=False,
            ):
                import api.main as main_api
                main_api = importlib.reload(main_api)
                health_readiness = main_api.health_readiness

                response = health_readiness(None)

            self.assertTrue(response["success"])
            data = response["data"]
            self.assertFalse(data["checks"]["audit_ready"])
            self.assertIn("audit_ready", data["failed_checks"])
            self.assertIn("audit_not_ready", data["reasons"])
            self.assertEqual(data["audit"]["table"], "")
            self.assertFalse(data["audit"]["validated"])
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
