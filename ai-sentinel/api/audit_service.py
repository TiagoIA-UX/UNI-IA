import os
from typing import Any, Dict, Optional

import requests


class AuditService:
    def __init__(self):
        self.supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.timeout_seconds = float(os.getenv("AUDIT_TIMEOUT_SECONDS", "10"))

    def is_ready(self) -> bool:
        return bool(self.supabase_url and self.service_role_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    def log_event(
        self,
        event_type: str,
        status: str,
        *,
        asset: Optional[str] = None,
        request_id: Optional[str] = None,
        classification: Optional[str] = None,
        score: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.is_ready():
            return {"success": False, "reason": "supabase_audit_nao_configurado"}

        payload = {
            "event_type": event_type,
            "status": status,
            "asset": asset,
            "request_id": request_id,
            "classification": classification,
            "score": score,
            "details": details or {},
        }

        response = requests.post(
            f"{self.supabase_url}/rest/v1/uni_ia_operational_audit",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(f"Falha ao persistir auditoria: HTTP {response.status_code} - {response.text[:300]}")

        return {"success": True}