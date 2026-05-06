import json
import os
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from core.system_state import SystemStateManager


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class KillSwitchService:
    def __init__(self):
        self.enabled = os.getenv("KILL_SWITCH_ENABLED", "true").strip().lower() == "true"
        self.max_daily_loss_pct = float(os.getenv("KILL_SWITCH_MAX_DAILY_LOSS_PCT", "3.0"))
        self.max_drawdown_pct = float(os.getenv("KILL_SWITCH_MAX_DRAWDOWN_PCT", "10.0"))
        self.window_days = int(os.getenv("KILL_SWITCH_WINDOW_DAYS", "1"))
        self.sample_limit = int(os.getenv("KILL_SWITCH_SAMPLE_LIMIT", "5000"))
        self._log_path = self._resolve_log_path()

    def _resolve_log_path(self) -> Path:
        configured = os.getenv("KILL_SWITCH_LOG_PATH", "")
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "risk_events.jsonl").resolve()

    def _append_event(self, payload: Dict[str, Any]):
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def get_recent_events(self, *, limit: int = 50, event_type: str | None = None) -> Dict[str, Any]:
        cap = max(min(int(limit), 500), 1)
        if not self._log_path.exists():
            return {
                "success": True,
                "count": 0,
                "items": [],
                "source": str(self._log_path),
            }

        normalized_event = event_type.strip().lower() if event_type else None
        rows: List[Dict[str, Any]] = []
        with self._log_path.open("r", encoding="utf-8") as fp:
            tail = deque(fp, maxlen=max(cap * 20, 200))

        for raw_line in tail:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue

            current_event = str(payload.get("event", "")).lower()
            if normalized_event and current_event != normalized_event:
                continue
            rows.append(payload)

        rows = rows[-cap:]
        rows.reverse()
        return {
            "success": True,
            "count": len(rows),
            "items": rows,
            "source": str(self._log_path),
        }

    def get_status(self, *, outcome_tracker, system_state: SystemStateManager) -> Dict[str, Any]:
        perf = outcome_tracker.compute_performance(
            window_days=self.window_days,
            sample_limit=self.sample_limit,
        )
        metrics = perf.get("metrics", {})
        total_pnl_pct = float(metrics.get("total_pnl_pct", 0.0))
        max_drawdown_pct = float(metrics.get("max_drawdown_pct", 0.0))
        recent = self.get_recent_events(limit=1)
        last_event = recent["items"][0] if recent.get("items") else None

        would_trigger = False
        if self.enabled:
            would_trigger = (
                total_pnl_pct <= -abs(self.max_daily_loss_pct)
                or max_drawdown_pct >= abs(self.max_drawdown_pct)
            )

        return {
            "enabled": self.enabled,
            "thresholds": {
                "max_daily_loss_pct": self.max_daily_loss_pct,
                "max_drawdown_pct": self.max_drawdown_pct,
                "window_days": self.window_days,
                "sample_limit": self.sample_limit,
            },
            "system": system_state.snapshot(),
            "metrics": {
                "total_pnl_pct": total_pnl_pct,
                "max_drawdown_pct": max_drawdown_pct,
            },
            "would_trigger_now": would_trigger,
            "last_event": last_event,
            "source": str(self._log_path),
        }

    def evaluate_or_raise(
        self,
        *,
        outcome_tracker,
        system_state: SystemStateManager,
        audit_service=None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"enabled": False, "triggered": False}

        perf = outcome_tracker.compute_performance(
            window_days=self.window_days,
            sample_limit=self.sample_limit,
        )
        metrics = perf.get("metrics", {})
        total_pnl_pct = float(metrics.get("total_pnl_pct", 0.0))
        max_drawdown_pct = float(metrics.get("max_drawdown_pct", 0.0))

        reasons: List[str] = []
        if total_pnl_pct <= -abs(self.max_daily_loss_pct):
            reasons.append(
                f"daily_loss_limit_reached:{total_pnl_pct:.6f}%<=-{abs(self.max_daily_loss_pct):.6f}%"
            )

        if max_drawdown_pct >= abs(self.max_drawdown_pct):
            reasons.append(
                f"drawdown_limit_reached:{max_drawdown_pct:.6f}%>={abs(self.max_drawdown_pct):.6f}%"
            )

        if not reasons:
            return {
                "enabled": True,
                "triggered": False,
                "metrics": {
                    "total_pnl_pct": total_pnl_pct,
                    "max_drawdown_pct": max_drawdown_pct,
                },
            }

        reason = "KILL_SWITCH_TRIGGERED: " + " | ".join(reasons)
        event = {
            "event": "kill_switch_triggered",
            "timestamp": _utcnow_iso(),
            "reasons": reasons,
            "metrics": {
                "total_pnl_pct": total_pnl_pct,
                "max_drawdown_pct": max_drawdown_pct,
            },
            "window_days": self.window_days,
        }

        self._append_event(event)
        system_state.set_halted(reason)

        if audit_service:
            audit_service.log_event(
                "risk.kill_switch",
                "halted",
                details=event,
            )

        raise RuntimeError(reason)
