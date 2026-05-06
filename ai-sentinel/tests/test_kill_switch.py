import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.kill_switch import KillSwitchService
from core.system_state import SystemStateManager, SystemStatus, UniIAMode


class _FakeOutcomeTracker:
    def __init__(self, *, total_pnl_pct: float, max_drawdown_pct: float):
        self.total_pnl_pct = total_pnl_pct
        self.max_drawdown_pct = max_drawdown_pct

    def compute_performance(self, **kwargs):
        return {
            "metrics": {
                "total_pnl_pct": self.total_pnl_pct,
                "max_drawdown_pct": self.max_drawdown_pct,
            }
        }


class KillSwitchTests(unittest.TestCase):
    def test_does_not_trigger_when_within_limits(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as fp:
            log_path = fp.name

        try:
            with patch.dict(
                os.environ,
                {
                    "KILL_SWITCH_ENABLED": "true",
                    "KILL_SWITCH_MAX_DAILY_LOSS_PCT": "3",
                    "KILL_SWITCH_MAX_DRAWDOWN_PCT": "10",
                    "KILL_SWITCH_LOG_PATH": log_path,
                },
                clear=False,
            ):
                service = KillSwitchService()
                state = SystemStateManager(UniIAMode.PAPER)
                state.apply_validation_result(critical_errors=[], non_critical_errors=[])
                result = service.evaluate_or_raise(
                    outcome_tracker=_FakeOutcomeTracker(total_pnl_pct=-1.0, max_drawdown_pct=2.5),
                    system_state=state,
                )

            self.assertTrue(result["enabled"])
            self.assertFalse(result["triggered"])
            self.assertEqual(state.status, SystemStatus.READY)
        finally:
            try:
                os.unlink(log_path)
            except Exception:
                pass

    def test_triggers_on_daily_loss_and_halts_system(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as fp:
            log_path = fp.name

        try:
            with patch.dict(
                os.environ,
                {
                    "KILL_SWITCH_ENABLED": "true",
                    "KILL_SWITCH_MAX_DAILY_LOSS_PCT": "3",
                    "KILL_SWITCH_MAX_DRAWDOWN_PCT": "10",
                    "KILL_SWITCH_LOG_PATH": log_path,
                },
                clear=False,
            ):
                service = KillSwitchService()
                state = SystemStateManager(UniIAMode.LIVE)
                state.apply_validation_result(critical_errors=[], non_critical_errors=[])
                fake_audit = MagicMock()

                with self.assertRaises(RuntimeError):
                    service.evaluate_or_raise(
                        outcome_tracker=_FakeOutcomeTracker(total_pnl_pct=-5.0, max_drawdown_pct=4.0),
                        system_state=state,
                        audit_service=fake_audit,
                    )

            self.assertEqual(state.status, SystemStatus.HALTED)
            fake_audit.log_event.assert_called_once()
            self.assertTrue(Path(log_path).read_text(encoding="utf-8").strip())
        finally:
            try:
                os.unlink(log_path)
            except Exception:
                pass

    def test_get_recent_events_returns_last_items(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as fp:
            fp.write('{"event":"kill_switch_triggered","timestamp":"2026-04-17T10:00:00Z"}\n')
            fp.write('{"event":"risk_notice","timestamp":"2026-04-17T11:00:00Z"}\n')
            log_path = fp.name

        try:
            with patch.dict(os.environ, {"KILL_SWITCH_LOG_PATH": log_path}, clear=False):
                service = KillSwitchService()
                recent = service.get_recent_events(limit=1)
                filtered = service.get_recent_events(limit=10, event_type="kill_switch_triggered")

            self.assertEqual(recent["count"], 1)
            self.assertEqual(recent["items"][0]["event"], "risk_notice")
            self.assertEqual(filtered["count"], 1)
            self.assertEqual(filtered["items"][0]["event"], "kill_switch_triggered")
        finally:
            try:
                os.unlink(log_path)
            except Exception:
                pass

    def test_get_status_returns_thresholds_and_metrics(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w", encoding="utf-8") as fp:
            fp.write('{"event":"kill_switch_triggered","timestamp":"2026-04-17T12:00:00Z"}\n')
            log_path = fp.name

        try:
            with patch.dict(
                os.environ,
                {
                    "KILL_SWITCH_ENABLED": "true",
                    "KILL_SWITCH_MAX_DAILY_LOSS_PCT": "3",
                    "KILL_SWITCH_MAX_DRAWDOWN_PCT": "10",
                    "KILL_SWITCH_LOG_PATH": log_path,
                },
                clear=False,
            ):
                service = KillSwitchService()
                state = SystemStateManager(UniIAMode.PAPER)
                state.apply_validation_result(critical_errors=[], non_critical_errors=[])
                status = service.get_status(
                    outcome_tracker=_FakeOutcomeTracker(total_pnl_pct=-4.0, max_drawdown_pct=2.0),
                    system_state=state,
                )

            self.assertTrue(status["enabled"])
            self.assertTrue(status["would_trigger_now"])
            self.assertEqual(status["last_event"]["event"], "kill_switch_triggered")
        finally:
            try:
                os.unlink(log_path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
