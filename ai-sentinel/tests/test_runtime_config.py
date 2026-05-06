import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.runtime_config import build_system_state, get_runtime_mode
from core.system_state import SystemStatus, UniIAMode


class _FakeAdapter:
    def __init__(self, ready=True, missing=None):
        self._ready = ready
        self._missing = missing or []

    def is_ready(self):
        return self._ready

    def missing_config(self):
        return self._missing


class _FakeCopyTradeService:
    def __init__(self, enabled=True, adapter=None):
        self.enabled = enabled
        self.adapter = adapter or _FakeAdapter()


class _FakeAuditService:
    def __init__(self, ready=True, fail_on_validate=False, error_message="audit_validation_error"):
        self._ready = ready
        self._fail_on_validate = fail_on_validate
        self._error_message = error_message

    def is_ready(self):
        return self._ready

    def validate_boot_or_raise(self):
        if self._fail_on_validate:
            raise RuntimeError(self._error_message)


class _FakeSignalScanner:
    def __init__(self, configured=True):
        self._configured = configured

    def configured(self):
        return self._configured


class _FakeTelegramControl:
    def __init__(self, configured=True):
        self._configured = configured

    def configured(self):
        return self._configured


class _FakeTelegramBot:
    def __init__(self, configured=True):
        self._configured = configured

    def configured(self):
        return self._configured


class _FakeDeskStore:
    def __init__(self, ready=True, missing=None):
        self._ready = ready
        self._missing = missing or []

    def is_ready(self):
        return self._ready

    def missing_config(self):
        return self._missing


class RuntimeConfigTests(unittest.TestCase):
    def setUp(self):
        self.base_env = {
            "UNI_IA_ADMIN_TOKEN": "secret",
            "UNI_IA_ALLOWED_ORIGINS": "http://localhost:3000",
            "UNI_IA_MODE": "paper",
            "UNI_IA_REQUIRE_APPROVAL": "true",
            "AUDIT_TABLE_NAME": "uni_ia_events",
            "SIGNAL_SCANNER_ENABLED": "false",
            "TELEGRAM_CONTROL_ENABLED": "false",
        }

    def _build_state(self, extra_env=None, **deps):
        env = {**self.base_env, **(extra_env or {})}
        with patch.dict(os.environ, env, clear=True):
            return build_system_state(
                copy_trade_service=deps.get("copy_trade_service", _FakeCopyTradeService()),
                audit_service=deps.get("audit_service", _FakeAuditService()),
                signal_scanner=deps.get("signal_scanner", _FakeSignalScanner()),
                telegram_control=deps.get("telegram_control", _FakeTelegramControl()),
                telegram_bot=deps.get("telegram_bot", _FakeTelegramBot()),
                desk_store=deps.get("desk_store", _FakeDeskStore()),
            )

    def test_invalid_mode_raises(self):
        with patch.dict(os.environ, {"UNI_IA_MODE": "broken-mode"}, clear=True):
            with self.assertRaises(RuntimeError):
                get_runtime_mode()

    def test_valid_config_becomes_ready(self):
        state = self._build_state()
        self.assertEqual(state.mode, UniIAMode.PAPER)
        self.assertEqual(state.status, SystemStatus.READY)

    def test_missing_admin_token_becomes_halted(self):
        state = self._build_state(extra_env={"UNI_IA_ADMIN_TOKEN": ""})
        self.assertEqual(state.status, SystemStatus.HALTED)

    def test_audit_ready_without_table_name_becomes_halted_even_in_paper(self):
        state = self._build_state(extra_env={"AUDIT_TABLE_NAME": ""})
        self.assertEqual(state.status, SystemStatus.HALTED)
        self.assertIn("Auditoria configurada exige AUDIT_TABLE_NAME definido explicitamente.", state.reasons)

    def test_partial_non_critical_config_becomes_degraded(self):
        state = self._build_state(
            extra_env={"TELEGRAM_CONTROL_ENABLED": "true"},
            telegram_control=_FakeTelegramControl(configured=False),
        )
        self.assertEqual(state.status, SystemStatus.DEGRADED)

    def test_approval_requires_audit_and_telegram_control(self):
        state = self._build_state(
            extra_env={"UNI_IA_MODE": "approval", "TELEGRAM_CONTROL_ENABLED": "true"},
            audit_service=_FakeAuditService(ready=False),
            telegram_control=_FakeTelegramControl(configured=False),
        )
        self.assertEqual(state.status, SystemStatus.HALTED)

    def test_live_without_broker_becomes_halted(self):
        state = self._build_state(
            extra_env={"UNI_IA_MODE": "live"},
            copy_trade_service=_FakeCopyTradeService(
                enabled=True,
                adapter=_FakeAdapter(ready=False, missing=["BROKER_API_KEY"]),
            ),
        )
        self.assertEqual(state.status, SystemStatus.HALTED)

    def test_live_without_audit_table_name_becomes_halted(self):
        state = self._build_state(extra_env={"UNI_IA_MODE": "live", "AUDIT_TABLE_NAME": ""})
        self.assertEqual(state.status, SystemStatus.HALTED)

    def test_approval_without_telegram_dispatch_becomes_halted(self):
        state = self._build_state(
            extra_env={"UNI_IA_MODE": "approval"},
            telegram_bot=_FakeTelegramBot(configured=False),
        )
        self.assertEqual(state.status, SystemStatus.HALTED)
        self.assertIn(
            "UNI_IA_MODE=approval/live exige Telegram de dispatch configurado com tokens e canais.",
            state.reasons,
        )

    def test_live_without_telegram_dispatch_becomes_halted(self):
        state = self._build_state(
            extra_env={"UNI_IA_MODE": "live"},
            telegram_bot=_FakeTelegramBot(configured=False),
        )
        self.assertEqual(state.status, SystemStatus.HALTED)

    def test_audit_validation_failure_becomes_halted(self):
        state = self._build_state(
            audit_service=_FakeAuditService(ready=True, fail_on_validate=True, error_message="table_not_found"),
        )
        self.assertEqual(state.status, SystemStatus.HALTED)


if __name__ == "__main__":
    unittest.main()
