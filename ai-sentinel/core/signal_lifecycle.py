from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from core.chart_timeframes import normalize_chart_timeframe


_TIMEFRAME_SECONDS = {
    "1m": 60,
    "2m": 120,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "90m": 5400,
    "4h": 14400,
    "1d": 86400,
    "1wk": 604800,
}


def timeframe_seconds(timeframe: Optional[str]) -> Optional[int]:
    tf = normalize_chart_timeframe(timeframe) if timeframe else None
    if tf == "1mo" or tf == "3mo":
        return None
    return _TIMEFRAME_SECONDS.get(tf or "")


def last_closed_candle_end(
    timeframe: Optional[str],
    *,
    now: Optional[datetime] = None,
    grace_seconds: int = 5,
) -> Optional[datetime]:
    """Returns the most recent candle close that is stable enough to confirm.

    Signals should be generated from this timestamp only. During the live candle,
    callers can run radar logic, but confirmed alerts must wait for this close.
    """
    seconds = timeframe_seconds(timeframe)
    if not seconds:
        return None
    ref = now or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    ts = int(ref.timestamp())
    close_ts = (ts // seconds) * seconds
    if ts - close_ts < max(int(grace_seconds), 0):
        close_ts -= seconds
    return datetime.fromtimestamp(close_ts, tz=timezone.utc)


def candle_key(asset: str, timeframe: Optional[str], candle_end: datetime) -> str:
    tf = normalize_chart_timeframe(timeframe) if timeframe else "n/a"
    return f"{asset.upper()}|{tf}|{candle_end.isoformat().replace('+00:00', 'Z')}"
