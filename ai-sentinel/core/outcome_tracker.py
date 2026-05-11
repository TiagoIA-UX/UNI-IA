"""Outcome Tracker — Correlacao signal -> execucao -> resultado final.

Registra o desfecho real de cada sinal emitido para habilitar:
- Win rate rolling por ativo/timeframe/estrategia
- Expectancy e profit factor
- Dataset supervisionado para evolucao de modelo

Persistencia: JSONL local + Supabase quando disponivel.
"""

import json
import os
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class OutcomeTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._log_path = self._resolve_log_path()
        self._supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self._service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self._timeout = float(os.getenv("OUTCOME_TRACKER_TIMEOUT_SECONDS", "10"))

    def _resolve_log_path(self) -> Path:
        configured = os.getenv("OUTCOME_LOG_PATH", "")
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "signal_outcomes.jsonl").resolve()

    def _supabase_ready(self) -> bool:
        return bool(self._supabase_url and self._service_role_key)

    def _supabase_headers(self) -> Dict[str, str]:
        return {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    # ------------------------------------------------------------------
    # Registro de outcome
    # ------------------------------------------------------------------

    def record_outcome(
        self,
        *,
        signal_id: str,
        request_id: Optional[str] = None,
        asset: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        pnl_percent: float,
        result: str,
        holding_seconds: Optional[float] = None,
        closed_at: Optional[str] = None,
        timeframe: Optional[str] = None,
        strategy: Optional[str] = None,
        model_version: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registra resultado final de um sinal.

        result: win | loss | timeout | breakeven
        """
        valid_results = {"win", "loss", "timeout", "breakeven"}
        normalized_result = result.lower().strip()
        if normalized_result not in valid_results:
            raise ValueError(f"result deve ser um de {valid_results}, recebeu: {result}")

        payload = {
            "signal_id": signal_id,
            "request_id": request_id,
            "asset": (asset or "").upper(),
            "direction": (direction or "").lower(),
            "entry_price": float(entry_price),
            "exit_price": float(exit_price),
            "pnl_percent": round(float(pnl_percent), 6),
            "result": normalized_result,
            "holding_seconds": float(holding_seconds) if holding_seconds is not None else None,
            "closed_at": closed_at or _utcnow_iso(),
            "recorded_at": _utcnow_iso(),
            "timeframe": timeframe,
            "strategy": strategy,
            "model_version": model_version or os.getenv("UNI_IA_MODEL_VERSION", "v1"),
            "extra": extra or {},
        }

        self._append_local(payload)
        supabase_result = self._persist_supabase(payload)
        return {"success": True, "signal_id": signal_id, "supabase": supabase_result}

    def _append_local(self, payload: Dict[str, Any]):
        with self._lock:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _persist_supabase(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._supabase_ready():
            return {"persisted": False, "reason": "supabase_nao_configurado"}
        try:
            response = requests.post(
                f"{self._supabase_url}/rest/v1/uni_ia_signal_outcomes",
                headers=self._supabase_headers(),
                json=payload,
                timeout=self._timeout,
            )
            if not response.ok:
                return {"persisted": False, "reason": f"HTTP {response.status_code}: {response.text[:200]}"}
            return {"persisted": True}
        except Exception as err:
            return {"persisted": False, "reason": str(err)}

    # ------------------------------------------------------------------
    # Leitura e metricas
    # ------------------------------------------------------------------

    def _iter_outcomes(self, limit: int = 5000):
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

    def get_recent_outcomes(
        self,
        *,
        limit: int = 50,
        asset: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        cap = max(min(int(limit), 500), 1)
        norm_asset = asset.upper().strip() if asset else None
        norm_strategy = strategy.lower().strip() if strategy else None

        rows: List[Dict[str, Any]] = []
        for item in self._iter_outcomes(limit=cap * 5):
            if norm_asset and str(item.get("asset", "")).upper() != norm_asset:
                continue
            if norm_strategy and str(item.get("strategy", "")).lower() != norm_strategy:
                continue
            rows.append(item)

        rows = rows[-cap:]
        rows.reverse()
        return {"success": True, "count": len(rows), "items": rows}

    def export_outcomes(
        self,
        *,
        limit: int = 50000,
        asset: Optional[str] = None,
        strategy: Optional[str] = None,
        result: Optional[str] = None,
        window_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        norm_asset = asset.upper().strip() if asset else None
        norm_strategy = strategy.lower().strip() if strategy else None
        norm_result = result.lower().strip() if result else None
        cutoff_ts = None
        if window_days is not None:
            cutoff_ts = datetime.now(timezone.utc).timestamp() - (max(int(window_days), 1) * 86400)

        rows: List[Dict[str, Any]] = []
        for item in self._iter_outcomes(limit=max(int(limit), 100)):
            if norm_asset and str(item.get("asset", "")).upper() != norm_asset:
                continue
            if norm_strategy and str(item.get("strategy", "")).lower() != norm_strategy:
                continue
            if norm_result and str(item.get("result", "")).lower() != norm_result:
                continue
            if cutoff_ts is not None:
                ts_raw = item.get("closed_at") or item.get("recorded_at")
                try:
                    event_ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp()
                except Exception:
                    continue
                if event_ts < cutoff_ts:
                    continue
            rows.append(item)
        return rows

    def compute_performance(
        self,
        *,
        window_days: int = 30,
        asset: Optional[str] = None,
        timeframe: Optional[str] = None,
        strategy: Optional[str] = None,
        sample_limit: int = 10000,
    ) -> Dict[str, Any]:
        """Calcula metricas rolling de performance live."""
        now = datetime.now(timezone.utc)
        cutoff_ts = now.timestamp() - (max(int(window_days), 1) * 86400)

        norm_asset = asset.upper().strip() if asset else None
        norm_tf = timeframe.strip() if timeframe else None
        norm_strat = strategy.lower().strip() if strategy else None

        considered: List[Dict[str, Any]] = []
        for item in self._iter_outcomes(limit=max(int(sample_limit), 100)):
            ts_raw = item.get("closed_at") or item.get("recorded_at")
            try:
                event_ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp()
            except Exception:
                continue
            if event_ts < cutoff_ts:
                continue
            if norm_asset and str(item.get("asset", "")).upper() != norm_asset:
                continue
            if norm_tf and str(item.get("timeframe", "")) != norm_tf:
                continue
            if norm_strat and str(item.get("strategy", "")).lower() != norm_strat:
                continue
            considered.append(item)

        total = len(considered)
        wins = sum(1 for x in considered if x.get("result") == "win")
        losses = sum(1 for x in considered if x.get("result") == "loss")
        timeouts = sum(1 for x in considered if x.get("result") == "timeout")
        breakevens = sum(1 for x in considered if x.get("result") == "breakeven")

        pnls = [float(x.get("pnl_percent", 0)) for x in considered]
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))

        win_rate = round((wins / total * 100), 4) if total else 0.0
        avg_win = round(gross_profit / wins, 6) if wins else 0.0
        avg_loss = round(gross_loss / losses, 6) if losses else 0.0
        expectancy = round(
            (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss), 6
        ) if total else 0.0
        profit_factor = round(gross_profit / gross_loss, 4) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0
        total_pnl = round(sum(pnls), 6)

        # Max drawdown (running sum)
        max_dd = 0.0
        peak = 0.0
        running = 0.0
        for p in pnls:
            running += p
            if running > peak:
                peak = running
            dd = peak - running
            if dd > max_dd:
                max_dd = dd
        max_dd = round(max_dd, 6)

        # Breakdown por ativo
        by_asset: Dict[str, Dict[str, Any]] = {}
        for item in considered:
            key = str(item.get("asset", "UNKNOWN")).upper()
            bucket = by_asset.setdefault(key, {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0})
            bucket["total"] += 1
            if item.get("result") == "win":
                bucket["wins"] += 1
            elif item.get("result") == "loss":
                bucket["losses"] += 1
            bucket["pnl"] = round(bucket["pnl"] + float(item.get("pnl_percent", 0)), 6)

        for key, bucket in by_asset.items():
            bucket["win_rate"] = round((bucket["wins"] / bucket["total"] * 100), 4) if bucket["total"] else 0.0

        return {
            "success": True,
            "generated_at": _utcnow_iso(),
            "filters": {
                "window_days": window_days,
                "asset": norm_asset,
                "timeframe": norm_tf,
                "strategy": norm_strat,
            },
            "totals": {
                "trades": total,
                "wins": wins,
                "losses": losses,
                "timeouts": timeouts,
                "breakevens": breakevens,
            },
            "metrics": {
                "win_rate": win_rate,
                "avg_win_pct": avg_win,
                "avg_loss_pct": avg_loss,
                "expectancy_pct": expectancy,
                "profit_factor": profit_factor,
                "total_pnl_pct": total_pnl,
                "max_drawdown_pct": max_dd,
            },
            "by_asset": by_asset,
        }

    def asset_hit_ranking(
        self,
        *,
        timeframe: str,
        window_days: int = 90,
        min_trades: int = 1,
        sample_limit: int = 20000,
    ) -> Dict[str, Any]:
        """Ranking de ativos por taxa de acerto (wins / decisivos) no timeframe informado.

        Usado para prioridade de execucao na mesa. Requer outcomes gravados com o mesmo
        valor em `timeframe` (ex: 5m, 1h) ao fechar posicao.
        """
        norm_tf = (timeframe or "").strip().lower()
        if not norm_tf:
            return {"timeframe": None, "window_days": window_days, "items": [], "note": "timeframe_vazio"}

        now = datetime.now(timezone.utc)
        cutoff_ts = now.timestamp() - (max(int(window_days), 1) * 86400)
        min_t = max(int(min_trades), 1)

        by_asset: Dict[str, Dict[str, int]] = {}
        for item in self._iter_outcomes(limit=max(int(sample_limit), 100)):
            if str(item.get("timeframe", "")).strip().lower() != norm_tf:
                continue
            ts_raw = item.get("closed_at") or item.get("recorded_at")
            try:
                event_ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00")).timestamp()
            except Exception:
                continue
            if event_ts < cutoff_ts:
                continue
            asset = str(item.get("asset", "")).upper().strip()
            if not asset:
                continue
            bucket = by_asset.setdefault(
                asset,
                {"wins": 0, "losses": 0, "timeouts": 0, "breakevens": 0},
            )
            res = str(item.get("result", "")).lower()
            if res == "win":
                bucket["wins"] += 1
            elif res == "loss":
                bucket["losses"] += 1
            elif res == "timeout":
                bucket["timeouts"] += 1
            elif res == "breakeven":
                bucket["breakevens"] += 1

        rows: List[Dict[str, Any]] = []
        for asset, b in by_asset.items():
            decisive = int(b["wins"]) + int(b["losses"])
            total = int(sum(b.values()))
            hit_rate = round((b["wins"] / decisive) * 100.0, 2) if decisive > 0 else 0.0
            if total < min_t:
                tier = "insuficiente"
            elif total >= 20:
                tier = "alta_amostra"
            elif total >= 8:
                tier = "media"
            else:
                tier = "inicial"
            rows.append(
                {
                    "asset": asset,
                    "trades": total,
                    "decisive_trades": decisive,
                    "wins": b["wins"],
                    "losses": b["losses"],
                    "timeouts": b["timeouts"],
                    "breakevens": b["breakevens"],
                    "hit_rate_pct": hit_rate,
                    "sample_tier": tier,
                }
            )

        rows.sort(key=lambda r: (-float(r["hit_rate_pct"]), -int(r["trades"]), r["asset"]))
        return {
            "timeframe": norm_tf,
            "window_days": int(window_days),
            "min_trades": min_t,
            "items": rows,
        }
