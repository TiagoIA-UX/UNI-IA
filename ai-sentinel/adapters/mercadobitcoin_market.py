from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


MB_PUBLIC_BASE = "https://api.mercadobitcoin.net/api/v4"
_CACHE_TTL_SECONDS = 5.0
_cache: Dict[str, tuple[float, Any]] = {}


def normalize_mb_market(asset: str) -> str:
    s = (asset or "").strip().upper().replace("/", "-").replace("_", "-")
    if not s:
        raise ValueError("asset vazio")
    if "-" in s:
        base, quote = s.split("-", 1)
        return f"{base}-{quote or 'BRL'}"
    if s.endswith("USDT") and len(s) > 4:
        return f"{s[:-4]}-BRL"
    if s.endswith("BRL") and len(s) > 3:
        return f"{s[:-3]}-BRL"
    return f"{s}-BRL"


def compact_mb_market(asset: str) -> str:
    return normalize_mb_market(asset).replace("-", "")


def _get_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: float = 8.0) -> Any:
    key = f"{url}?{params or {}}"
    now = time.time()
    cached = _cache.get(key)
    if cached and now - cached[0] <= _CACHE_TTL_SECONDS:
        return cached[1]
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    _cache[key] = (now, data)
    return data


def get_ticker(asset: str) -> Dict[str, Any]:
    market = normalize_mb_market(asset)
    data = _get_json(f"{MB_PUBLIC_BASE}/tickers", params={"symbols": market})
    ticker = data[0] if isinstance(data, list) and data else data
    if not isinstance(ticker, dict):
        raise ValueError(f"ticker MB invalido para {market}")

    def num(*keys: str) -> Optional[float]:
        for key in keys:
            value = ticker.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return None

    last = num("last", "lastPrice", "close")
    if last is None or last <= 0:
        raise ValueError(f"ticker MB sem ultimo preco valido para {market}")
    return {
        "market": market,
        "last": last,
        "high": num("high", "high24h"),
        "low": num("low", "low24h"),
        "volume": num("volume", "vol"),
        "raw": ticker,
    }


def get_candles(asset: str, granularity_seconds: int, limit: int = 120) -> List[Dict[str, Any]]:
    market = normalize_mb_market(asset)
    end = int(time.time())
    start = end - max(int(granularity_seconds) * max(int(limit), 10), int(granularity_seconds) * 20)
    resolution_map = {
        60: "1m",
        120: "1m",
        300: "1m",
        900: "15m",
        1800: "15m",
        3600: "1h",
        5400: "1h",
        14400: "1h",
        86400: "1d",
        604800: "1w",
    }
    resolution = resolution_map.get(int(granularity_seconds), "15m")
    data = _get_json(
        f"{MB_PUBLIC_BASE}/candles",
        params={"symbol": market, "resolution": resolution, "from": start, "to": end, "countback": max(int(limit), 10)},
    )
    if isinstance(data, dict) and all(k in data for k in ("t", "o", "h", "l", "c")):
        rows = list(zip(
            data.get("t", []),
            data.get("o", []),
            data.get("h", []),
            data.get("l", []),
            data.get("c", []),
            data.get("v", []),
        ))
    else:
        rows = data.get("candles") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError(f"candles MB invalidos para {market}")
    out: List[Dict[str, Any]] = []
    for row in rows[-limit:]:
        if isinstance(row, dict):
            ts = row.get("timestamp") or row.get("time") or row.get("t")
            open_ = row.get("open") or row.get("o")
            high = row.get("high") or row.get("h")
            low = row.get("low") or row.get("l")
            close = row.get("close") or row.get("c")
            volume = row.get("volume") or row.get("v")
        elif isinstance(row, list) and len(row) >= 6:
            ts, open_, high, low, close, volume = row[:6]
        else:
            continue
        try:
            ts_i = int(float(ts))
            if ts_i > 10_000_000_000:
                ts_i //= 1000
            out.append(
                {
                    "time": datetime.fromtimestamp(ts_i, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
                    "timestamp": ts_i,
                    "open": float(open_),
                    "high": float(high),
                    "low": float(low),
                    "close": float(close),
                    "volume": float(volume or 0),
                }
            )
        except (TypeError, ValueError, OSError):
            continue
    out.sort(key=lambda item: item["timestamp"])
    return out
