"""Sentinel Decision Store — persistencia estruturada da governanca por signal_id.

Governanca nao e feature. Esta store registra a decisao formal do SENTINEL,
permite exportacao supervisionada com outcome e computa metricas economicas por regime.
"""

import json
import math
import os
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from core.contract_validation import normalize_sentinel_decision, require_float, require_non_empty_string, require_percentage


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SentinelDecisionStore:
    SCHEMA_VERSION = 1

    def __init__(self):
        self._lock = threading.Lock()
        self._log_path = self._resolve_log_path()
        self._supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self._service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self._timeout = float(os.getenv("SENTINEL_DECISION_STORE_TIMEOUT_SECONDS", "10"))

    def _resolve_log_path(self) -> Path:
        configured = os.getenv("SENTINEL_DECISION_LOG_PATH", "")
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "sentinel_decisions.jsonl").resolve()

    def _supabase_ready(self) -> bool:
        return bool(self._supabase_url and self._service_role_key)

    def _supabase_headers(self) -> Dict[str, str]:
        return {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    def _sanitize_for_json(self, value: Any):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                raise RuntimeError("sentinel_decision_store recebeu valor numerico nao finito.")
            return value
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return {str(key): self._sanitize_for_json(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._sanitize_for_json(item) for item in value]
        return str(value)

    def record_decision(
        self,
        *,
        signal_id: str,
        asset: str,
        regime_id: str,
        regime_version: str,
        sentinel_decision: str,
        sentinel_confidence: float,
        block_reason_code: str,
        expected_confidence_delta: float,
        approved: bool,
        reason_codes: List[str],
        risk_flags: List[str],
        regime_confidence: Optional[float] = None,
        score: Optional[float] = None,
        classification: Optional[str] = None,
        direction: Optional[str] = None,
        timeframe: Optional[str] = None,
        strategy_confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized_signal_id = require_non_empty_string(signal_id, "signal_id")
        normalized_asset = require_non_empty_string(asset, "asset").upper()
        normalized_regime_id = require_non_empty_string(regime_id, "regime_id")
        normalized_regime_version = require_non_empty_string(regime_version, "regime_version")
        normalized_decision = normalize_sentinel_decision(sentinel_decision, "sentinel_decision")
        normalized_reason_code = require_non_empty_string(block_reason_code, "block_reason_code")
        normalized_reason_codes = [require_non_empty_string(item, "reason_codes") for item in reason_codes]
        normalized_risk_flags = [require_non_empty_string(item, "risk_flags") for item in risk_flags]

        payload = {
            "signal_id": normalized_signal_id,
            "asset": normalized_asset,
            "regime_id": normalized_regime_id,
            "regime_version": normalized_regime_version,
            "regime_confidence": require_percentage(regime_confidence, "regime_confidence") if regime_confidence is not None else None,
            "sentinel_decision": normalized_decision,
            "sentinel_confidence": require_percentage(sentinel_confidence, "sentinel_confidence"),
            "block_reason_code": normalized_reason_code,
            "expected_confidence_delta": round(require_float(expected_confidence_delta, "expected_confidence_delta"), 6),
            "approved": bool(approved),
            "reason_codes": normalized_reason_codes,
            "risk_flags": normalized_risk_flags,
            "score": round(require_percentage(score, "score"), 6) if score is not None else None,
            "classification": classification,
            "direction": direction,
            "timeframe": timeframe,
            "strategy_confidence": round(require_percentage(strategy_confidence, "strategy_confidence"), 6) if strategy_confidence is not None else None,
            "recorded_at": _utcnow_iso(),
            "model_version": os.getenv("UNI_IA_MODEL_VERSION", "v1"),
            "sentinel_schema_version": self.SCHEMA_VERSION,
            "metadata": self._sanitize_for_json(metadata or {}),
        }

        self._append_local(payload)
        supabase = self._persist_supabase(payload)
        return {"success": True, "signal_id": normalized_signal_id, "sentinel_decision": normalized_decision, "supabase": supabase}

    def _append_local(self, payload: Dict[str, Any]):
        with self._lock:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

    def _persist_supabase(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._supabase_ready():
            return {"persisted": False, "reason": "supabase_nao_configurado"}
        try:
            response = requests.post(
                f"{self._supabase_url}/rest/v1/uni_ia_sentinel_decisions",
                headers=self._supabase_headers(),
                json=payload,
                timeout=self._timeout,
            )
            if not response.ok:
                return {"persisted": False, "reason": f"HTTP {response.status_code}: {response.text[:200]}"}
            return {"persisted": True}
        except Exception as err:
            return {"persisted": False, "reason": str(err)}

    def _iter_entries(self, limit: int = 10000):
        if not self._log_path.exists():
            return
        with self._log_path.open("r", encoding="utf-8") as fp:
            tail = deque(fp, maxlen=max(int(limit), 1))
        for raw in tail:
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj

    def export_decisions(
        self,
        *,
        limit: int = 50000,
        asset: Optional[str] = None,
        regime_id: Optional[str] = None,
        regime_version: Optional[str] = None,
        sentinel_decision: Optional[str] = None,
        approved: Optional[bool] = None,
        window_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        norm_asset = asset.upper().strip() if asset else None
        norm_regime_id = regime_id.strip().lower() if regime_id else None
        norm_regime_version = regime_version.strip() if regime_version else None
        norm_decision = sentinel_decision.strip().lower() if sentinel_decision else None
        cutoff_ts = None
        if window_days is not None:
            cutoff_ts = datetime.now(timezone.utc).timestamp() - (max(int(window_days), 1) * 86400)

        rows: List[Dict[str, Any]] = []
        for item in self._iter_entries(limit=max(int(limit), 100)):
            if norm_asset and str(item.get("asset", "")).upper() != norm_asset:
                continue
            if norm_regime_id and str(item.get("regime_id", "")).strip().lower() != norm_regime_id:
                continue
            if norm_regime_version and str(item.get("regime_version", "")).strip() != norm_regime_version:
                continue
            if norm_decision and str(item.get("sentinel_decision", "")).strip().lower() != norm_decision:
                continue
            if approved is not None and bool(item.get("approved")) != bool(approved):
                continue
            if cutoff_ts is not None:
                ts_raw = item.get("recorded_at")
                try:
                    event_ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp()
                except Exception:
                    continue
                if event_ts < cutoff_ts:
                    continue
            rows.append(item)
        return rows

    def get_decision_for_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        normalized_signal_id = str(signal_id or "").strip()
        if not normalized_signal_id:
            return None
        for item in reversed(self.export_decisions(limit=50000)):
            if str(item.get("signal_id", "")).strip() == normalized_signal_id:
                return item
        return None

    def export_supervised_dataset(
        self,
        *,
        outcome_tracker,
        limit: int = 50000,
        asset: Optional[str] = None,
        regime_id: Optional[str] = None,
        regime_version: Optional[str] = None,
        sentinel_decision: Optional[str] = None,
        window_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        rows = self.export_decisions(
            limit=limit,
            asset=asset,
            regime_id=regime_id,
            regime_version=regime_version,
            sentinel_decision=sentinel_decision,
            window_days=window_days,
        )
        outcome_rows = outcome_tracker.export_outcomes(
            asset=asset,
            limit=max(limit * 3, 100),
            window_days=window_days,
        )
        outcome_by_signal = {row.get("signal_id"): row for row in outcome_rows if row.get("signal_id")}

        items: List[Dict[str, Any]] = []
        missing_outcome = 0
        for row in rows:
            outcome = outcome_by_signal.get(row.get("signal_id"))
            if not outcome:
                missing_outcome += 1
            items.append(
                {
                    "decision": row,
                    "outcome": outcome,
                }
            )

        return {
            "success": True,
            "count": len(items),
            "missing_outcome": missing_outcome,
            "items": items,
        }

    def compute_regime_metrics(
        self,
        *,
        outcome_tracker,
        limit: int = 50000,
        asset: Optional[str] = None,
        regime_id: Optional[str] = None,
        regime_version: Optional[str] = None,
        window_days: int = 90,
    ) -> Dict[str, Any]:
        decisions = self.export_decisions(
            limit=limit,
            asset=asset,
            regime_id=regime_id,
            regime_version=regime_version,
            window_days=window_days,
        )
        outcome_rows = outcome_tracker.export_outcomes(
            asset=asset,
            limit=max(limit * 3, 100),
            window_days=window_days,
        )
        outcome_by_signal = {row.get("signal_id"): row for row in outcome_rows if row.get("signal_id")}

        regimes: Dict[str, Dict[str, Any]] = {}
        for row in decisions:
            bucket_key = f"{row.get('regime_id')}::{row.get('regime_version')}"
            bucket = regimes.setdefault(
                bucket_key,
                {
                    "regime_id": row.get("regime_id"),
                    "regime_version": row.get("regime_version"),
                    "total_signals": 0,
                    "allowed_count": 0,
                    "blocked_count": 0,
                    "downgraded_count": 0,
                    "evaluated_blocked_count": 0,
                    "unevaluated_blocked_count": 0,
                    "false_block_count": 0,
                    "alpha_lost_total_pct": 0.0,
                    "false_block_avg_pnl_pct": 0.0,
                    "drawdown_avoided_count": 0,
                    "drawdown_avoided_total_pct": 0.0,
                    "governance_value_pct": 0.0,
                },
            )
            bucket["total_signals"] += 1

            decision = str(row.get("sentinel_decision") or "").lower()
            if decision == "allow":
                bucket["allowed_count"] += 1
            elif decision == "block":
                bucket["blocked_count"] += 1
            elif decision == "downgrade":
                bucket["downgraded_count"] += 1

            if decision != "block":
                continue

            outcome = outcome_by_signal.get(row.get("signal_id"))
            if not outcome:
                bucket["unevaluated_blocked_count"] += 1
                continue

            bucket["evaluated_blocked_count"] += 1
            pnl_percent = float(outcome.get("pnl_percent", 0.0) or 0.0)
            result = str(outcome.get("result", "")).lower()
            if result == "win" and pnl_percent > 0:
                bucket["false_block_count"] += 1
                bucket["alpha_lost_total_pct"] = round(bucket["alpha_lost_total_pct"] + pnl_percent, 6)
            elif result == "loss" and pnl_percent < 0:
                bucket["drawdown_avoided_count"] += 1
                bucket["drawdown_avoided_total_pct"] = round(bucket["drawdown_avoided_total_pct"] + abs(pnl_percent), 6)

        for bucket in regimes.values():
            blocked_count = bucket["blocked_count"]
            total_signals = bucket["total_signals"]
            evaluated_blocked = bucket["evaluated_blocked_count"]
            bucket["block_rate_pct"] = round((blocked_count / total_signals) * 100, 4) if total_signals else 0.0
            bucket["false_block_rate_pct"] = round((bucket["false_block_count"] / evaluated_blocked) * 100, 4) if evaluated_blocked else 0.0
            bucket["false_block_avg_pnl_pct"] = round((bucket["alpha_lost_total_pct"] / bucket["false_block_count"]), 6) if bucket["false_block_count"] else 0.0
            bucket["governance_value_pct"] = round(
                bucket["drawdown_avoided_total_pct"] - bucket["alpha_lost_total_pct"],
                6,
            )

        return {
            "success": True,
            "window_days": window_days,
            "count": len(decisions),
            "regimes": list(regimes.values()),
        }