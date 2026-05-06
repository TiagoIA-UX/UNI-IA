import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


class ArgusApiFlowTests(unittest.TestCase):
    def test_register_then_close_uses_same_argus_registry(self):
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
                    "UNI_IA_ADMIN_TOKEN": "test-token",
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

                register = main_api.argus_register(
                    {
                        "signal_id": "sig-argus-1",
                        "request_id": "req-argus-1",
                        "asset": "BTCUSDT",
                        "direction": "long",
                        "entry_price": 100.0,
                        "timeframe": "15m",
                        "strategy": "swing",
                    },
                    _=None,
                )
                close = main_api.argus_close(
                    {
                        "signal_id": "sig-argus-1",
                        "exit_price": 105.0,
                        "result": "win",
                    },
                    _=None,
                )

            self.assertTrue(register["success"])
            self.assertTrue(close["success"])
            self.assertTrue(close["data"]["closed"])
            self.assertEqual(close["data"]["signal_id"], "sig-argus-1")
            self.assertEqual(close["data"]["outcome"]["signal_id"], "sig-argus-1")
        finally:
            for path in (outcome_file.name, dispatch_file.name, risk_file.name):
                try:
                    os.unlink(path)
                except Exception:
                    pass

    def test_outcome_record_requires_known_active_position_when_request_id_is_absent(self):
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
                    "UNI_IA_ADMIN_TOKEN": "test-token",
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

                main_api.argus_register(
                    {
                        "signal_id": "sig-argus-2",
                        "asset": "BTCUSDT",
                        "direction": "long",
                        "entry_price": 100.0,
                        "timeframe": "15m",
                        "strategy": "swing",
                    },
                    _=None,
                )

                outcome = main_api.outcomes_record(
                    {
                        "signal_id": "sig-argus-2",
                        "asset": "BTCUSDT",
                        "direction": "long",
                        "entry_price": 100.0,
                        "exit_price": 103.0,
                        "pnl_percent": 3.0,
                        "result": "win",
                    },
                    _=None,
                )

            self.assertTrue(outcome["success"])
            self.assertEqual(outcome["data"]["signal_id"], "sig-argus-2")
        finally:
            for path in (outcome_file.name, dispatch_file.name, risk_file.name):
                try:
                    os.unlink(path)
                except Exception:
                    pass

    def test_outcome_record_fails_without_correlation(self):
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
                    "UNI_IA_ADMIN_TOKEN": "test-token",
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

                with self.assertRaises(Exception) as ctx:
                    main_api.outcomes_record(
                        {
                            "signal_id": "sig-orfao",
                            "asset": "BTCUSDT",
                            "direction": "long",
                            "entry_price": 100.0,
                            "exit_price": 103.0,
                            "pnl_percent": 3.0,
                            "result": "win",
                        },
                        _=None,
                    )

            self.assertIn("correlacao verificavel", str(ctx.exception))
        finally:
            for path in (outcome_file.name, dispatch_file.name, risk_file.name):
                try:
                    os.unlink(path)
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()