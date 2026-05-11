import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class AdminArgusHttpTests(unittest.TestCase):
    def test_admin_routes_require_token(self):
        outcome_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        dispatch_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        risk_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        outcome_file.close()
        dispatch_file.close()
        risk_file.close()

        try:
            with patch.dict(
                os.environ,
                {
                    "UNI_IA_ADMIN_TOKEN": "adm-secret-test",
                    "AUDIT_TABLE_NAME": "uni_ia_events",
                    "AUDIT_EVENT_VARIANT": "A",
                    "UNI_IA_ALLOWED_ORIGINS": "http://localhost:3000",
                    "UNI_IA_MODE": "paper",
                    "COPY_TRADE_ENABLED": "false",
                    "OUTCOME_LOG_PATH": outcome_file.name,
                    "SIGNAL_DISPATCH_LOG_PATH": dispatch_file.name,
                    "KILL_SWITCH_LOG_PATH": risk_file.name,
                    "NEXT_PUBLIC_SUPABASE_URL": "",
                    "SUPABASE_SERVICE_ROLE_KEY": "",
                },
                clear=False,
            ):
                import api.main as main_api

                main_api = importlib.reload(main_api)
                client = TestClient(main_api.app)

                r = client.post(
                    "/api/admin/argus/register",
                    json={
                        "signal_id": "http-sig-1",
                        "asset": "BTCUSDT",
                        "direction": "long",
                        "entry_price": 100.0,
                    },
                )
                self.assertEqual(r.status_code, 401)

                r2 = client.post(
                    "/api/admin/argus/register",
                    json={
                        "signal_id": "http-sig-1",
                        "asset": "BTCUSDT",
                        "direction": "long",
                        "entry_price": 100.0,
                    },
                    headers={"X-UNI-IA-ADMIN-TOKEN": "wrong"},
                )
                self.assertEqual(r2.status_code, 401)

                r3 = client.post(
                    "/api/admin/argus/register",
                    json={
                        "signal_id": "http-sig-1",
                        "asset": "BTCUSDT",
                        "direction": "long",
                        "entry_price": 100.0,
                    },
                    headers={"X-UNI-IA-ADMIN-TOKEN": "adm-secret-test"},
                )
                self.assertEqual(r3.status_code, 200)
                self.assertTrue(r3.json().get("success"))

                r4 = client.post(
                    "/api/admin/argus/close",
                    json={
                        "signal_id": "http-sig-1",
                        "exit_price": 105.0,
                        "result": "win",
                    },
                    headers={"X-UNI-IA-ADMIN-TOKEN": "adm-secret-test"},
                )
                self.assertEqual(r4.status_code, 200)
                self.assertTrue(r4.json().get("success"))
        finally:
            for path in (outcome_file.name, dispatch_file.name, risk_file.name):
                try:
                    os.unlink(path)
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()
