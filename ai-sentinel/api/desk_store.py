import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DeskStoreService:
    def __init__(self):
        self.supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.timeout_seconds = float(os.getenv("DESK_STORE_TIMEOUT_SECONDS", "10"))

    def is_ready(self) -> bool:
        return bool(self.supabase_url and self.service_role_key)

    def missing_config(self) -> List[str]:
        missing = []
        if not self.supabase_url:
            missing.append("NEXT_PUBLIC_SUPABASE_URL")
        if not self.service_role_key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        return missing

    def _headers(self, *, return_representation: bool = False) -> Dict[str, str]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
        }
        headers["Prefer"] = "return=representation" if return_representation else "return=minimal"
        return headers

    def create_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_ready()
        response = requests.post(
            f"{self.supabase_url}/rest/v1/uni_ia_desk_requests",
            headers=self._headers(return_representation=True),
            json=payload,
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(
                f"Falha ao persistir pendencia da mesa: HTTP {response.status_code} - {response.text[:300]}"
            )
        rows = response.json()
        return rows[0] if rows else payload

    def list_pending(self) -> List[Dict[str, Any]]:
        self._ensure_ready()
        response = requests.get(
            f"{self.supabase_url}/rest/v1/uni_ia_desk_requests",
            headers=self._headers(),
            params={
                "status": "eq.pending_approval",
                "select": "*",
                "order": "created_at.desc",
            },
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(
                f"Falha ao listar pendencias da mesa: HTTP {response.status_code} - {response.text[:300]}"
            )
        return response.json()

    def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_ready()
        response = requests.get(
            f"{self.supabase_url}/rest/v1/uni_ia_desk_requests",
            headers=self._headers(),
            params={
                "request_id": f"eq.{request_id}",
                "select": "*",
                "limit": 1,
            },
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(
                f"Falha ao carregar request da mesa: HTTP {response.status_code} - {response.text[:300]}"
            )
        rows = response.json()
        return rows[0] if rows else None

    def mark_executed(self, request_id: str, execution: Dict[str, Any]) -> Dict[str, Any]:
        return self._update_request(
            request_id,
            {
                "status": "executed",
                "execution": execution,
                "executed_at": _utc_now_iso(),
            },
            expected_current_status="pending_approval",
        )

    def mark_rejected(self, request_id: str, reason: str) -> Dict[str, Any]:
        return self._update_request(
            request_id,
            {
                "status": "rejected",
                "reason": reason,
                "rejected_at": _utc_now_iso(),
            },
            expected_current_status="pending_approval",
        )

    def _update_request(
        self,
        request_id: str,
        payload: Dict[str, Any],
        *,
        expected_current_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_ready()
        params = {
            "request_id": f"eq.{request_id}",
            "select": "*",
        }
        if expected_current_status:
            params["status"] = f"eq.{expected_current_status}"

        response = requests.patch(
            f"{self.supabase_url}/rest/v1/uni_ia_desk_requests",
            headers=self._headers(return_representation=True),
            params=params,
            json=payload,
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(
                f"Falha ao atualizar request da mesa: HTTP {response.status_code} - {response.text[:300]}"
        )
        rows = response.json()
        if not rows:
            raise RuntimeError("Request da mesa nao encontrada ou nao esta mais pendente.")
        return rows[0]

    def _ensure_ready(self):
        if not self.is_ready():
            raise RuntimeError(
                "Persistencia da mesa nao configurada. Defina NEXT_PUBLIC_SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY."
            )
