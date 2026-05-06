import json
import os
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso_utc(ts_raw: str) -> datetime:
    return datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).astimezone(timezone.utc)


class DailyOpsReportService:
    def __init__(self):
        self._dispatch_log_path = self._resolve_dispatch_log_path()
        self._risk_log_path = self._resolve_risk_log_path()

    def _resolve_dispatch_log_path(self) -> Path:
        configured_path = os.getenv("SIGNAL_DISPATCH_LOG_PATH", "")
        if configured_path:
            return Path(configured_path).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "signal_dispatch.jsonl").resolve()

    def _resolve_risk_log_path(self) -> Path:
        configured_path = os.getenv("KILL_SWITCH_LOG_PATH", "")
        if configured_path:
            return Path(configured_path).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "risk_events.jsonl").resolve()

    def _iter_events(self) -> List[Dict[str, Any]]:
        if not self._dispatch_log_path.exists():
            raise RuntimeError(f"dispatch_log_not_found: {self._dispatch_log_path}")

        rows: List[Dict[str, Any]] = []
        with self._dispatch_log_path.open("r", encoding="utf-8") as fp:
            for raw_line in fp:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    def _iter_risk_events(self) -> List[Dict[str, Any]]:
        if not self._risk_log_path.exists():
            return []

        rows: List[Dict[str, Any]] = []
        with self._risk_log_path.open("r", encoding="utf-8") as fp:
            for raw_line in fp:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except Exception:
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    def _is_risk_reason(self, reason: str) -> bool:
        normalized = (reason or "").lower()
        markers = [
            "risk",
            "exposure",
            "drawdown",
            "kill_switch",
            "halted",
            "bloqueou",
            "blocked",
        ]
        return any(marker in normalized for marker in markers)

    def generate_daily_report(self, *, report_date: date | None = None) -> Dict[str, Any]:
        target_date = report_date or datetime.now(timezone.utc).date()
        window_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        window_end = window_start + timedelta(days=1)

        all_rows = self._iter_events()
        rows: List[Dict[str, Any]] = []
        for item in all_rows:
            try:
                ts = _parse_iso_utc(item.get("timestamp"))
            except Exception:
                continue
            if window_start <= ts < window_end:
                rows.append(item)

        reason_counter: Counter[str] = Counter()
        by_asset: Dict[str, Dict[str, int]] = {}

        signals_generated = len(rows)
        signals_blocked = 0
        signals_failed = 0
        signals_executed = 0
        risk_events = 0

        for item in rows:
            status = str(item.get("status", "")).lower()
            scanner_result = item.get("scanner_result", {}) if isinstance(item.get("scanner_result"), dict) else {}
            reason = str(scanner_result.get("reason") or item.get("error") or "unknown")
            asset = str(item.get("asset", "UNKNOWN")).upper()
            desk_action = str(scanner_result.get("desk_action", "")).lower()

            bucket = by_asset.setdefault(asset, {"generated": 0, "blocked": 0, "failed": 0, "executed": 0})
            bucket["generated"] += 1

            if status == "blocked":
                signals_blocked += 1
                bucket["blocked"] += 1
                reason_counter[reason] += 1
                if self._is_risk_reason(reason):
                    risk_events += 1

            if status == "failed":
                signals_failed += 1
                bucket["failed"] += 1
                if self._is_risk_reason(reason):
                    risk_events += 1

            if desk_action == "executed":
                signals_executed += 1
                bucket["executed"] += 1

        top_reasons = [{"reason": reason, "count": count} for reason, count in reason_counter.most_common(5)]

        risk_rows = []
        for item in self._iter_risk_events():
            try:
                ts = _parse_iso_utc(item.get("timestamp"))
            except Exception:
                continue
            if window_start <= ts < window_end:
                risk_rows.append(item)

        risk_events = max(risk_events, len(risk_rows))

        return {
            "success": True,
            "generated_at": _utcnow_iso(),
            "window": {
                "date": target_date.isoformat(),
                "timezone": "UTC",
                "start": window_start.isoformat().replace("+00:00", "Z"),
                "end": window_end.isoformat().replace("+00:00", "Z"),
            },
            "totals": {
                "signals_generated": signals_generated,
                "signals_blocked": signals_blocked,
                "signals_failed": signals_failed,
                "executed": signals_executed,
                "risk_events": risk_events,
            },
            "top_reasons_block": top_reasons,
            "by_asset": by_asset,
            "source": {
                "dispatch_log_path": str(self._dispatch_log_path),
                "risk_log_path": str(self._risk_log_path),
            },
        }
