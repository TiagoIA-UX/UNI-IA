import os
from typing import Any, Dict, Optional

import requests


class AuditService:
    def __init__(self):
        self.supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.timeout_seconds = float(os.getenv("AUDIT_TIMEOUT_SECONDS", "10"))
        self.audit_table_name = os.getenv("AUDIT_TABLE_NAME", "").strip()

    SUPPORTED_AUDIT_TABLES = {
        "uni_ia_operational_audit",
        "uni_ia_events",
    }

    def is_ready(self) -> bool:
        return bool(self.supabase_url and self.service_role_key)

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    def _validate_contract_or_raise(self):
        if not self.audit_table_name:
            raise RuntimeError("AUDIT_TABLE_NAME obrigatorio.")

        if self.audit_table_name not in self.SUPPORTED_AUDIT_TABLES:
            raise RuntimeError(f"AUDIT_TABLE_NAME nao suportado: {self.audit_table_name}")

        if self.audit_table_name == "uni_ia_events":
            variant = os.getenv("AUDIT_EVENT_VARIANT", "A").strip().upper()
            if variant not in {"A", "B"}:
                raise RuntimeError(f"AUDIT_EVENT_VARIANT invalido: {variant}")

    def validate_boot_or_raise(self):
        self._validate_contract_or_raise()
        if not self.is_ready():
            raise RuntimeError("auditoria_supabase_nao_configurada")

        response = requests.get(
            f"{self.supabase_url}/rest/v1/{self.audit_table_name}?select=*&limit=1",
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(
                "auditoria_tabela_invalida_ou_inexistente: "
                f"{self.audit_table_name} (HTTP {response.status_code})"
            )

    def _build_payload(
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
        self._validate_contract_or_raise()

        # Contrato operacional atual.
        if self.audit_table_name == "uni_ia_operational_audit":
            return {
                "event_type": event_type,
                "status": status,
                "asset": asset,
                "request_id": request_id,
                "classification": classification,
                "score": score,
                "details": details or {},
            }

        # Contrato legado de eventos da plataforma.
        if self.audit_table_name == "uni_ia_events":
            variant = os.getenv("AUDIT_EVENT_VARIANT", "A").strip().upper()

            return {
                "event": event_type,
                "page": os.getenv("AUDIT_EVENT_PAGE", "ai-sentinel-operational"),
                "variant": variant,
                "locale": os.getenv("AUDIT_EVENT_LOCALE", "pt-BR"),
                "event_ts": None,
                "details": {
                    "status": status,
                    "asset": asset,
                    "request_id": request_id,
                    "classification": classification,
                    "score": score,
                    **(details or {}),
                },
            }

        raise RuntimeError("Contrato de auditoria invalido apos validacao.")

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

        payload = self._build_payload(
            event_type,
            status,
            asset=asset,
            request_id=request_id,
            classification=classification,
            score=score,
            details=details,
        )

        response = requests.post(
            f"{self.supabase_url}/rest/v1/{self.audit_table_name}",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(f"Falha ao persistir auditoria: HTTP {response.status_code} - {response.text[:300]}")

        return {"success": True}