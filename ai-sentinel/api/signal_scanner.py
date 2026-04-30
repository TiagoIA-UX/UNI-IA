import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List

from core.schemas import OpportunityAlert


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class SignalScanner:
    def __init__(self, analysis_service, telegram_bot, private_desk, audit_service=None):
        self.analysis_service = analysis_service
        self.telegram_bot = telegram_bot
        self.private_desk = private_desk
        self.audit_service = audit_service
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

    def _is_eligible(self, alert: OpportunityAlert, cfg: Dict[str, Any]) -> bool:
        if float(alert.score) < cfg["min_score"]:
            return False
        if cfg["allowed_classifications"] and alert.classification.upper() not in cfg["allowed_classifications"]:
            return False
        return True

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
            "config": cfg,
            "cycle_count": self._cycle_count,
            "last_cycle_started_at": self._last_cycle_started_at,
            "last_cycle_completed_at": self._last_cycle_completed_at,
            "last_error": self._last_error,
            "last_results": self._last_results,
            "recent_alerts": self._recent_alerts,
        }

    def _dispatch_alert(self, alert: OpportunityAlert) -> Dict[str, Any]:
        preview = self.private_desk.preview_action(alert)
        telegram_result = {"success": True, "dispatched": True}
        try:
            self.telegram_bot.dispatch_alert(alert, operational_context=preview)
        except Exception as telegram_error:
            telegram_result = {
                "success": False,
                "dispatched": False,
                "error": str(telegram_error),
            }

        desk_result = self.private_desk.handle_alert(alert)
        return {
            "preview": preview,
            "telegram": telegram_result,
            "desk": desk_result,
        }

    def _audit(self, event_type: str, status: str, **payload):
        if not self.audit_service:
            return
        try:
            self.audit_service.log_event(event_type, status, **payload)
        except Exception as err:
            self._last_error = str(err)

    def scan_asset(self, asset: str) -> Dict[str, Any]:
        cfg = self._cfg()
        try:
            alert = self.analysis_service.analyze(asset)
            result: Dict[str, Any] = {
                "asset": asset.upper(),
                "classification": alert.classification,
                "score": alert.score,
                "dispatched": False,
                "desk_action": "ignored",
            }

            if not self._is_eligible(alert, cfg):
                result["reason"] = "fora_do_filtro"
                return result

            if self._is_duplicate(alert, cfg["dedupe_ttl_seconds"]):
                result["reason"] = "duplicado_no_intervalo"
                return result

            dispatch_result = self._dispatch_alert(alert)
            result["dispatched"] = bool(dispatch_result["telegram"].get("dispatched"))
            result["desk_action"] = dispatch_result["desk"].get("action")
            if dispatch_result["desk"].get("request_id"):
                result["request_id"] = dispatch_result["desk"]["request_id"]
            result["operational_status"] = dispatch_result["preview"].get("operational_status")
            self._audit(
                "signal.generated",
                "success",
                asset=alert.asset,
                request_id=result.get("request_id"),
                classification=alert.classification,
                score=float(alert.score),
                details={
                    "scanner_result": result,
                    "strategy": alert.strategy.dict() if alert.strategy else None,
                    "telegram": dispatch_result["telegram"],
                    "desk_preview": dispatch_result["preview"],
                },
            )

            self._remember_alert(alert, result, cfg["recent_limit"])
            return result
        except Exception as err:
            self._last_error = str(err)
            return {
                "asset": asset.upper(),
                "error": str(err),
            }

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