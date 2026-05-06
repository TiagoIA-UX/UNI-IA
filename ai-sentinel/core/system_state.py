from enum import Enum
from typing import Any, Dict, List, Optional


class UniIAMode(str, Enum):
    PAPER = "paper"
    APPROVAL = "approval"
    LIVE = "live"


class SystemStatus(str, Enum):
    LOCKED = "locked"
    READY = "ready"
    DEGRADED = "degraded"
    HALTED = "halted"


class SystemStateManager:
    def __init__(self, mode: UniIAMode):
        self.mode = mode
        self.status = SystemStatus.LOCKED
        self.reasons: List[str] = []

    def apply_validation_result(self, *, critical_errors: List[str], non_critical_errors: List[str]):
        reasons = [*critical_errors, *non_critical_errors]
        self.reasons = reasons

        if critical_errors:
            self._transition_to(SystemStatus.HALTED, reason_list=reasons, force=True)
            return

        if non_critical_errors:
            self._transition_to(SystemStatus.DEGRADED, reason_list=reasons, force=True)
            return

        self._transition_to(SystemStatus.READY, reason_list=[], force=True)

    def set_locked(self, reason: Optional[str] = None):
        self._transition_to(SystemStatus.LOCKED, reason_list=[reason] if reason else [], force=True)

    def set_halted(self, reason: str):
        self._transition_to(SystemStatus.HALTED, reason_list=[reason], force=True)

    def transition_to(self, next_status: SystemStatus, reason: Optional[str] = None):
        self._transition_to(next_status, reason_list=[reason] if reason else [])

    def _transition_to(self, next_status: SystemStatus, *, reason_list: List[str], force: bool = False):
        allowed = {
            SystemStatus.LOCKED: {SystemStatus.READY, SystemStatus.HALTED},
            SystemStatus.READY: {SystemStatus.DEGRADED, SystemStatus.HALTED},
            SystemStatus.DEGRADED: {SystemStatus.READY},
            SystemStatus.HALTED: {SystemStatus.LOCKED},
        }

        if not force and next_status != self.status and next_status not in allowed[self.status]:
            raise RuntimeError(
                f"Transicao de status proibida: {self.status.value} -> {next_status.value}."
            )

        if not force and self.status == SystemStatus.HALTED and next_status == SystemStatus.READY:
            raise RuntimeError("HALTED -> READY automatico e proibido.")

        self.status = next_status
        self.reasons = reason_list

    def snapshot(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "status": self.status.value,
            "reasons": self.reasons,
        }

    def can_generate_signal(self) -> bool:
        if self.status == SystemStatus.HALTED:
            return False
        if self.status == SystemStatus.LOCKED:
            return False
        return self.status in {SystemStatus.READY, SystemStatus.DEGRADED}

    def can_create_pending(self) -> bool:
        if self.status == SystemStatus.HALTED:
            return False
        if self.mode == UniIAMode.PAPER:
            return False
        return self.status in {SystemStatus.READY, SystemStatus.DEGRADED}

    def can_execute_live(self) -> bool:
        return self.mode == UniIAMode.LIVE and self.status == SystemStatus.READY

    def require_signal_generation(self):
        if not self.can_generate_signal():
            raise RuntimeError(
                f"Sistema bloqueado para gerar sinais (mode={self.mode.value}, status={self.status.value})."
            )

    def require_pending_creation(self):
        if not self.can_create_pending():
            raise RuntimeError(
                f"Sistema bloqueado para criar pendencias (mode={self.mode.value}, status={self.status.value})."
            )

    def require_live_execution(self):
        if not self.can_execute_live():
            raise RuntimeError(
                f"Execucao real bloqueada (mode={self.mode.value}, status={self.status.value})."
            )
