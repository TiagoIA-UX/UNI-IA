import os
import json
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from core.contract_validation import normalize_classification
from core.execution_integrity import ExecutionIntegrityError
from core.schemas import OpportunityAlert, model_to_dict


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class SignalScanner:
    def __init__(self, analysis_service, telegram_bot, private_desk, audit_service=None, system_state=None, integrity_guard=None):
        self.analysis_service = analysis_service
        self.telegram_bot = telegram_bot
        self.private_desk = private_desk
        self.audit_service = audit_service
        self.system_state = system_state
        self.integrity_guard = integrity_guard
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._thread = None
        self._cycle_count = 0
        self._last_cycle_started_at = None
        self._last_cycle_completed_at = None
        self._last_error = None
        self._last_results: List[Dict[str, Any]] = []
        self._recent_alerts: List[Dict[str, Any]] = []
        self._dedupe_cache: Dict[str, float] = {}
        self._dispatch_log_lock = threading.Lock()
        self._dispatch_log_path = self._resolve_dispatch_log_path()

    def _resolve_dispatch_log_path(self) -> Path:
        configured_path = os.getenv("SIGNAL_DISPATCH_LOG_PATH", "")
        if configured_path:
            return Path(configured_path).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "signal_dispatch.jsonl").resolve()

    def _append_dispatch_log(self, payload: Dict[str, Any]):
        try:
            with self._dispatch_log_lock:
                self._dispatch_log_path.parent.mkdir(parents=True, exist_ok=True)
                with self._dispatch_log_path.open("a", encoding="utf-8") as fp:
                    fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception as err:
            self._last_error = str(err)

    def _iter_dispatch_events(self, limit: int = 1000):
        max_items = max(int(limit), 1)
        if not self._dispatch_log_path.exists():
            return
        with self._dispatch_log_path.open("r", encoding="utf-8") as fp:
            tail = deque(fp, maxlen=max_items)
        for raw_line in tail:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                yield payload

    def get_recent_dispatch_events(
        self,
        *,
        limit: int = 50,
        status: str | None = None,
        asset: str | None = None,
    ) -> Dict[str, Any]:
        normalized_status = status.lower().strip() if status else None
        normalized_asset = asset.upper().strip() if asset else None
        cap = max(min(int(limit), 500), 1)
        source_limit = max(cap * 10, 200)

        rows: List[Dict[str, Any]] = []
        for event in self._iter_dispatch_events(limit=source_limit):
            if normalized_status and str(event.get("status", "")).lower() != normalized_status:
                continue
            if normalized_asset and str(event.get("asset", "")).upper() != normalized_asset:
                continue
            rows.append(event)

        rows = rows[-cap:]
        rows.reverse()
        return {
            "success": True,
            "count": len(rows),
            "filters": {
                "limit": cap,
                "status": normalized_status,
                "asset": normalized_asset,
            },
            "items": rows,
        }

    def get_dispatch_metrics(self, *, window_minutes: int = 1440, sample_limit: int = 5000) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        window = max(int(window_minutes), 1)
        sample_cap = max(int(sample_limit), 100)
        cutoff_ts = now.timestamp() - (window * 60)

        considered = []
        for event in self._iter_dispatch_events(limit=sample_cap):
            ts_raw = event.get("timestamp")
            try:
                event_ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp()
            except Exception:
                continue
            if event_ts >= cutoff_ts:
                considered.append(event)

        total = len(considered)
        sent = sum(1 for item in considered if str(item.get("status", "")).lower() == "sent")
        failed = sum(1 for item in considered if str(item.get("status", "")).lower() == "failed")
        blocked = sum(1 for item in considered if str(item.get("status", "")).lower() == "blocked")

        def _pct(value: int) -> float:
            return round((value / total * 100.0), 4) if total else 0.0

        by_asset: Dict[str, Dict[str, int]] = {}
        for item in considered:
            key = str(item.get("asset", "UNKNOWN")).upper()
            bucket = by_asset.setdefault(key, {"total": 0, "sent": 0, "failed": 0, "blocked": 0})
            bucket["total"] += 1
            state = str(item.get("status", "")).lower()
            if state in bucket:
                bucket[state] += 1

        return {
            "success": True,
            "window_minutes": window,
            "sample_limit": sample_cap,
            "generated_at": _utcnow_iso(),
            "totals": {
                "events": total,
                "sent": sent,
                "failed": failed,
                "blocked": blocked,
            },
            "rates": {
                "sent_percent": _pct(sent),
                "failed_percent": _pct(failed),
                "blocked_percent": _pct(blocked),
            },
            "by_asset": by_asset,
        }

    def _record_dispatch_event(
        self,
        *,
        signal_id: str,
        status: str,
        alert: OpportunityAlert,
        scanner_result: Dict[str, Any],
        preview: Dict[str, Any] | None = None,
        telegram: Dict[str, Any] | None = None,
        desk: Dict[str, Any] | None = None,
        error: str | None = None,
    ):
        strategy = alert.strategy
        payload = {
            "signal_id": signal_id,
            "timestamp": _utcnow_iso(),
            "asset": alert.asset,
            "classification": alert.classification,
            "score": float(alert.score),
            "timeframe": strategy.timeframe if strategy else None,
            "strategy": strategy.mode if strategy else None,
            "mandate": {
                "desk_mode": (preview or {}).get("mode"),
                "action": (preview or {}).get("action"),
                "operational_status": (preview or {}).get("operational_status"),
            },
            "status": status,
            "scanner_result": scanner_result,
            "telegram": telegram or {},
            "desk": desk or {},
            "error": error,
        }
        self._append_dispatch_log(payload)

    def _cfg(self) -> Dict[str, Any]:
        assets_raw = os.getenv("SIGNAL_SCAN_ASSETS", "")
        allowed_classifications_raw = os.getenv("SIGNAL_ALLOWED_CLASSIFICATIONS", "OPORTUNIDADE")
        assets = [asset.strip().upper() for asset in assets_raw.split(",") if asset.strip()]
        allowed_classifications = [
            item.strip().upper() for item in allowed_classifications_raw.split(",") if item.strip()
        ]
        return {
            "enabled": os.getenv("SIGNAL_SCANNER_ENABLED", "false").lower() == "true",
            "assets": assets,
            "interval_seconds": max(float(os.getenv("SIGNAL_SCAN_INTERVAL_SECONDS", "60")), 10.0),
            "stagger_seconds": max(float(os.getenv("SIGNAL_SCAN_STAGGER_SECONDS", "2")), 0.0),
            "min_score": float(os.getenv("SIGNAL_MIN_SCORE", "75")),
            "allowed_classifications": allowed_classifications,
            "dedupe_ttl_seconds": max(float(os.getenv("SIGNAL_DEDUPE_TTL_SECONDS", "300")), 30.0),
            "recent_limit": max(int(os.getenv("SIGNAL_RECENT_LIMIT", "20")), 5),
            "session_filter_enabled": os.getenv("SIGNAL_SESSION_FILTER_ENABLED", "false").lower() == "true",
        }

    def _prune_dedupe_cache(self, ttl_seconds: float):
        now = time.time()
        expired_keys = [key for key, created_at in self._dedupe_cache.items() if now - created_at > ttl_seconds]
        for key in expired_keys:
            self._dedupe_cache.pop(key, None)

    def _signature(self, alert: OpportunityAlert) -> str:
        explanation = (alert.explanation or "").strip().upper()[:160]
        return "|".join(
            [
                (alert.asset or "").upper(),
                (alert.classification or "").upper(),
                str(int(round(float(alert.score)))),
                explanation,
            ]
        )

    def _is_duplicate(self, alert: OpportunityAlert, ttl_seconds: float) -> bool:
        self._prune_dedupe_cache(ttl_seconds)
        signature = self._signature(alert)
        created_at = self._dedupe_cache.get(signature)
        if created_at is None:
            return False
        return (time.time() - created_at) <= ttl_seconds

    def _remember_alert(self, alert: OpportunityAlert, result: Dict[str, Any], recent_limit: int):
        signature = self._signature(alert)
        self._dedupe_cache[signature] = time.time()
        item = {
            "asset": alert.asset,
            "classification": alert.classification,
            "score": alert.score,
            "explanation": alert.explanation,
            "captured_at": _utcnow_iso(),
            "result": result,
        }
        self._recent_alerts.insert(0, item)
        self._recent_alerts = self._recent_alerts[:recent_limit]

    def _is_in_trading_session(self) -> bool:
        """Retorna True se o horario UTC atual estiver numa janela de alta liquidez.

        Janelas (UTC):
        - Sessao asiatica:   00:00 - 04:00  (crypto: maior volatilidadé asiatica)
        - London open:       07:00 - 10:00
        - NY open + overlap: 13:00 - 17:00
        """
        hour = datetime.now(timezone.utc).hour
        WINDOWS = [(0, 4), (7, 10), (13, 17)]
        return any(start <= hour < end for start, end in WINDOWS)

    def _is_eligible(self, alert: OpportunityAlert, cfg: Dict[str, Any]) -> bool:
        if float(alert.score) < cfg["min_score"]:
            return False
        if cfg["allowed_classifications"] and normalize_classification(alert.classification) not in cfg["allowed_classifications"]:
            return False
        return True

    def _strict_operational_mode(self) -> bool:
        if self.system_state:
            return self.system_state.mode.value in {"approval", "live"}
        return os.getenv("UNI_IA_MODE", "paper").lower() in {"approval", "live"}

    def _dispatch_telegram(self, alert: OpportunityAlert, preview: Dict[str, Any]) -> Dict[str, Any]:
        if self._strict_operational_mode():
            self.telegram_bot.dispatch_alert(alert, operational_context=preview)
            return {"success": True, "dispatched": True}

        try:
            self.telegram_bot.dispatch_alert(alert, operational_context=preview)
            return {"success": True, "dispatched": True}
        except Exception as telegram_error:
            return {
                "success": False,
                "dispatched": False,
                "error": str(telegram_error),
            }

    def configured(self) -> bool:
        return len(self._cfg()["assets"]) > 0

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, force: bool = False) -> Dict[str, Any]:
        cfg = self._cfg()
        if not force and not cfg["enabled"]:
            return {"started": False, "reason": "scanner_desativado_por_config"}
        if not cfg["assets"]:
            return {"started": False, "reason": "nenhum_ativo_configurado"}

        with self._lock:
            if self.is_running():
                return {"started": False, "reason": "scanner_ja_ativo"}
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name="uni-ia-signal-scanner", daemon=True)
            self._thread.start()

        return {"started": True, "assets": cfg["assets"]}

    def stop(self) -> Dict[str, Any]:
        thread = None
        with self._lock:
            thread = self._thread
            self._stop_event.set()
        if thread and thread.is_alive():
            thread.join(timeout=2)
        with self._lock:
            self._thread = None
        return {"stopped": True}

    def status(self) -> Dict[str, Any]:
        cfg = self._cfg()
        return {
            "running": self.is_running(),
            "configured": self.configured(),
            "system": self.system_state.snapshot() if self.system_state else None,
            "config": cfg,
            "cycle_count": self._cycle_count,
            "last_cycle_started_at": self._last_cycle_started_at,
            "last_cycle_completed_at": self._last_cycle_completed_at,
            "last_error": self._last_error,
            "last_results": self._last_results,
            "recent_alerts": self._recent_alerts,
            "dispatch_log_path": str(self._dispatch_log_path),
        }

    def _dispatch_alert(self, alert: OpportunityAlert) -> Dict[str, Any]:
        stage = "integrity_guard"
        try:
            if self.integrity_guard is not None:
                self.integrity_guard.validate_dispatch_ready(alert)

            stage = "desk_preview"
            preview = self.private_desk.preview_action(alert)

            stage = "telegram_dispatch"
            telegram_result = self._dispatch_telegram(alert, preview)

            stage = "desk_dispatch"
            desk_result = self.private_desk.handle_alert(alert)
            return {
                "preview": preview,
                "telegram": telegram_result,
                "desk": desk_result,
            }
        except Exception as err:
            setattr(err, "signal_scanner_stage", stage)
            raise

    def _audit(self, event_type: str, status: str, **payload):
        if not self.audit_service:
            return
        try:
            self.audit_service.log_event(event_type, status, **payload)
        except Exception as err:
            self._last_error = str(err)

    def scan_asset(self, asset: str) -> Dict[str, Any]:
        cfg = self._cfg()
        signal_id = str(uuid.uuid4())
        if self.system_state and not self.system_state.can_generate_signal():
            blocked_result = {
                "asset": asset.upper(),
                "classification": "BLOCKED",
                "score": 0,
                "dispatched": False,
                "desk_action": "blocked",
                "reason": f"sistema_{self.system_state.status.value}",
                "signal_id": signal_id,
            }
            self._append_dispatch_log(
                {
                    "signal_id": signal_id,
                    "timestamp": _utcnow_iso(),
                    "asset": asset.upper(),
                    "classification": "BLOCKED",
                    "score": 0.0,
                    "timeframe": None,
                    "strategy": None,
                    "mandate": {},
                    "status": "blocked",
                    "scanner_result": blocked_result,
                    "telegram": {},
                    "desk": {},
                    "error": blocked_result["reason"],
                }
            )
            return blocked_result
        if cfg.get("session_filter_enabled") and not self._is_in_trading_session():
            skipped_result = {
                "asset": asset.upper(),
                "classification": "SKIPPED",
                "score": 0,
                "dispatched": False,
                "desk_action": "ignored",
                "reason": "fora_da_janela_de_sessao",
                "signal_id": signal_id,
            }
            self._append_dispatch_log(
                {
                    "signal_id": signal_id,
                    "timestamp": _utcnow_iso(),
                    "asset": asset.upper(),
                    "classification": "SKIPPED",
                    "score": 0.0,
                    "timeframe": None,
                    "strategy": None,
                    "mandate": {},
                    "status": "blocked",
                    "scanner_result": skipped_result,
                    "telegram": {},
                    "desk": {},
                    "error": skipped_result["reason"],
                }
            )
            return skipped_result
        try:
            alert = self.analysis_service.analyze(asset, signal_id=signal_id)
            result: Dict[str, Any] = {
                "asset": asset.upper(),
                "classification": alert.classification,
                "score": alert.score,
                "dispatched": False,
                "desk_action": "ignored",
                "signal_id": signal_id,
            }

            if not self._is_eligible(alert, cfg):
                result["reason"] = "fora_do_filtro"
                self._record_dispatch_event(
                    signal_id=signal_id,
                    status="blocked",
                    alert=alert,
                    scanner_result=result,
                    error=result["reason"],
                )
                return result

            if self._is_duplicate(alert, cfg["dedupe_ttl_seconds"]):
                result["reason"] = "duplicado_no_intervalo"
                self._record_dispatch_event(
                    signal_id=signal_id,
                    status="blocked",
                    alert=alert,
                    scanner_result=result,
                    error=result["reason"],
                )
                return result

            dispatch_result = self._dispatch_alert(alert)
            result["dispatched"] = bool(dispatch_result["telegram"].get("dispatched"))
            result["desk_action"] = dispatch_result["desk"].get("action")
            if dispatch_result["desk"].get("request_id"):
                result["request_id"] = dispatch_result["desk"]["request_id"]
            result["operational_status"] = dispatch_result["preview"].get("operational_status")
            dispatch_status = "sent" if result["dispatched"] else "failed"
            self._record_dispatch_event(
                signal_id=signal_id,
                status=dispatch_status,
                alert=alert,
                scanner_result=result,
                preview=dispatch_result["preview"],
                telegram=dispatch_result["telegram"],
                desk=dispatch_result["desk"],
                error=dispatch_result["telegram"].get("error"),
            )
            self._audit(
                "signal.generated",
                "success",
                asset=alert.asset,
                request_id=result.get("request_id"),
                classification=alert.classification,
                score=float(alert.score),
                details={
                    "scanner_result": result,
                    "strategy": model_to_dict(alert.strategy) if alert.strategy else None,
                    "telegram": dispatch_result["telegram"],
                    "desk_preview": dispatch_result["preview"],
                    "signal_id": signal_id,
                },
            )

            self._remember_alert(alert, result, cfg["recent_limit"])
            return result
        except Exception as err:
            self._last_error = str(err)
            error_result = {
                "asset": asset.upper(),
                "error": str(err),
                "signal_id": signal_id,
                "error_type": err.__class__.__name__,
                "error_stage": getattr(err, "signal_scanner_stage", "analysis"),
            }
            if isinstance(err, ExecutionIntegrityError):
                error_result["reason"] = str(err)
            self._append_dispatch_log(
                {
                    "signal_id": signal_id,
                    "timestamp": _utcnow_iso(),
                    "asset": asset.upper(),
                    "classification": "ERROR",
                    "score": 0.0,
                    "timeframe": None,
                    "strategy": None,
                    "mandate": {},
                    "status": "failed",
                    "scanner_result": error_result,
                    "telegram": {},
                    "desk": {},
                    "error": str(err),
                }
            )
            return error_result

    def run_cycle(self) -> Dict[str, Any]:
        cfg = self._cfg()
        if not cfg["assets"]:
            return {"success": False, "reason": "nenhum_ativo_configurado"}

        self._cycle_count += 1
        self._last_cycle_started_at = _utcnow_iso()
        results = []

        for index, asset in enumerate(cfg["assets"]):
            if self._stop_event.is_set():
                break
            results.append(self.scan_asset(asset))
            if index < len(cfg["assets"]) - 1 and cfg["stagger_seconds"] > 0:
                time.sleep(cfg["stagger_seconds"])

        self._last_cycle_completed_at = _utcnow_iso()
        self._last_results = results
        return {
            "success": True,
            "results": results,
            "cycle_count": self._cycle_count,
        }

    def _run_loop(self):
        while not self._stop_event.is_set():
            self.run_cycle()
            interval_seconds = self._cfg()["interval_seconds"]
            waited_seconds = 0.0
            while waited_seconds < interval_seconds and not self._stop_event.is_set():
                time.sleep(min(1.0, interval_seconds - waited_seconds))
                waited_seconds += 1.0
