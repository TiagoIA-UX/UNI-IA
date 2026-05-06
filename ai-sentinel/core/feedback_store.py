"""Feedback Store — Registro de feedback humano por signal_id.

Cada sinal emitido pode receber avaliacao humana (positivo/negativo)
via Telegram ou API. Esse dado alimenta o RewardModel para calibrar
os pesos dos agentes ao longo do tempo.

Persistencia: JSONL local + Supabase quando disponivel.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


VALID_RATINGS = {"positive", "negative"}


class FeedbackStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._log_path = self._resolve_log_path()
        self._supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self._service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self._timeout = float(os.getenv("FEEDBACK_STORE_TIMEOUT_SECONDS", "10"))

    def _resolve_log_path(self) -> Path:
        configured = os.getenv("FEEDBACK_LOG_PATH", "")
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "signal_feedback.jsonl").resolve()

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
    # Registro de feedback
    # ------------------------------------------------------------------

    def record_feedback(
        self,
        *,
        signal_id: str,
        rating: str,
        source: str = "telegram",
        reviewer_id: Optional[str] = None,
        asset: Optional[str] = None,
        agents_involved: Optional[List[str]] = None,
        comment: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Registra avaliacao humana de um sinal.

        rating: positive | negative
        source: telegram | api | manual
        """
        normalized_rating = rating.lower().strip()
        if normalized_rating not in VALID_RATINGS:
            raise ValueError(f"rating deve ser um de {VALID_RATINGS}, recebeu: {rating!r}")

        normalized_signal_id = str(signal_id or "").strip()
        if not normalized_signal_id:
            raise ValueError("signal_id obrigatorio para registrar feedback.")

        payload: Dict[str, Any] = {
            "signal_id": normalized_signal_id,
            "rating": normalized_rating,
            "source": str(source or "telegram").strip(),
            "reviewer_id": str(reviewer_id or "").strip() or None,
            "asset": str(asset or "").strip().upper() or None,
            "agents_involved": agents_involved or [],
            "comment": str(comment or "").strip() or None,
            "recorded_at": _utcnow_iso(),
            **(extra or {}),
        }

        self._persist_local(payload)
        self._persist_supabase(payload)
        return payload

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def get_feedback_for_signal(self, signal_id: str) -> List[Dict[str, Any]]:
        """Retorna todos os feedbacks registrados para um signal_id."""
        results = []
        if not self._log_path.exists():
            return results
        target = str(signal_id).strip()
        with self._lock:
            with self._log_path.open("r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("signal_id") == target:
                            results.append(entry)
                    except json.JSONDecodeError:
                        continue
        return results

    def get_recent_feedback(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Retorna os N feedbacks mais recentes."""
        if not self._log_path.exists():
            return []
        max_items = max(int(limit), 1)
        results: List[Dict[str, Any]] = []
        with self._lock:
            with self._log_path.open("r", encoding="utf-8") as fp:
                lines = fp.readlines()
        for line in lines[-max_items:]:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return results

    def stats(self, limit: int = 500) -> Dict[str, Any]:
        """Resumo agregado de feedback: total, positive_rate, por agente."""
        entries = self.get_recent_feedback(limit=limit)
        total = len(entries)
        if total == 0:
            return {"total": 0, "positive": 0, "negative": 0, "positive_rate": None, "by_agent": {}}

        positive = sum(1 for e in entries if e.get("rating") == "positive")
        negative = total - positive

        by_agent: Dict[str, Dict[str, int]] = {}
        for entry in entries:
            for agent in entry.get("agents_involved", []):
                if agent not in by_agent:
                    by_agent[agent] = {"positive": 0, "negative": 0}
                if entry.get("rating") == "positive":
                    by_agent[agent]["positive"] += 1
                else:
                    by_agent[agent]["negative"] += 1

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_rate": round(positive / total, 4),
            "by_agent": by_agent,
        }

    # ------------------------------------------------------------------
    # Persistencia interna
    # ------------------------------------------------------------------

    def _persist_local(self, payload: Dict[str, Any]) -> None:
        try:
            with self._lock:
                self._log_path.parent.mkdir(parents=True, exist_ok=True)
                with self._log_path.open("a", encoding="utf-8") as fp:
                    fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except Exception as err:
            raise RuntimeError(f"FeedbackStore: falha ao persistir localmente: {err}") from err

    def _persist_supabase(self, payload: Dict[str, Any]) -> None:
        if not self._supabase_ready():
            return
        try:
            url = f"{self._supabase_url}/rest/v1/signal_feedback"
            requests.post(
                url,
                headers=self._supabase_headers(),
                json=payload,
                timeout=self._timeout,
            )
        except Exception:
            # Supabase e melhor esforco — falha silenciosa
            pass
