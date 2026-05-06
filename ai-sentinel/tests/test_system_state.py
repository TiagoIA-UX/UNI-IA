import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.system_state import SystemStateManager, SystemStatus, UniIAMode


class SystemStateManagerTests(unittest.TestCase):
    def test_initial_status_is_locked(self):
        state = SystemStateManager(UniIAMode.PAPER)
        self.assertEqual(state.status, SystemStatus.LOCKED)

    def test_live_locked_never_executes(self):
        state = SystemStateManager(UniIAMode.LIVE)
        self.assertFalse(state.can_execute_live())

    def test_invalid_transition_raises(self):
        state = SystemStateManager(UniIAMode.LIVE)
        with self.assertRaises(RuntimeError):
            state.transition_to(SystemStatus.DEGRADED)

    def test_halted_to_ready_automatic_is_impossible(self):
        state = SystemStateManager(UniIAMode.LIVE)
        state.transition_to(SystemStatus.HALTED, reason="critical_failure")

        with self.assertRaises(RuntimeError):
            state.transition_to(SystemStatus.READY)

    def test_halted_requires_manual_return_to_locked_before_ready(self):
        state = SystemStateManager(UniIAMode.LIVE)
        state.transition_to(SystemStatus.HALTED, reason="critical_failure")
        state.transition_to(SystemStatus.LOCKED, reason="manual_reset")
        state.transition_to(SystemStatus.READY, reason="validated")

        self.assertEqual(state.status, SystemStatus.READY)


if __name__ == "__main__":
    unittest.main()
