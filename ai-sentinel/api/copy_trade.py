import os
from typing import Dict, Any
import requests
from ..core.schemas import OpportunityAlert


class BrokerAdapter:
    """Adapter HTTP generico para broker/exchange.

    Espera endpoints reais no broker configurado:
    - POST /orders
    - GET /orders/{order_id}
    """

    def __init__(self):
        self.base_url = os.getenv("BROKER_API_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("BROKER_API_KEY", "")
        self.account_id = os.getenv("BROKER_ACCOUNT_ID", "")
        self.timeout_seconds = float(os.getenv("BROKER_TIMEOUT_SECONDS", "10"))

    def is_ready(self) -> bool:
        return bool(self.base_url and self.api_key and self.account_id)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Account-Id": self.account_id,
        }

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError("Broker nao configurado. Defina BROKER_API_BASE_URL, BROKER_API_KEY e BROKER_ACCOUNT_ID.")

        response = requests.post(
            f"{self.base_url}/orders",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(f"Erro ao enviar ordem ao broker: HTTP {response.status_code} - {response.text[:300]}")
        return response.json()


class CopyTradeService:
    def __init__(self):
        self.enabled = os.getenv("COPY_TRADE_ENABLED", "false").lower() == "true"
        self.min_confidence = int(os.getenv("COPY_TRADE_MIN_CONFIDENCE", "75"))
        self.max_risk_percent = float(os.getenv("COPY_TRADE_MAX_RISK_PERCENT", "1.0"))
        self.adapter = BrokerAdapter()

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "broker_ready": self.adapter.is_ready(),
            "min_confidence": self.min_confidence,
            "max_risk_percent": self.max_risk_percent,
        }

    def _validate_signal_for_copytrade(self, alert: OpportunityAlert):
        if not self.enabled:
            raise RuntimeError("Copy trade desativado (COPY_TRADE_ENABLED=false).")
        if not self.adapter.is_ready():
            raise RuntimeError("Copy trade bloqueado: broker nao configurado.")
        if alert.classification != "OPORTUNIDADE":
            raise RuntimeError("Copy trade bloqueado: apenas sinais OPORTUNIDADE sao elegiveis.")
        if alert.score < self.min_confidence:
            raise RuntimeError(f"Copy trade bloqueado: score abaixo do minimo ({alert.score} < {self.min_confidence}).")

    def execute_from_alert(self, alert: OpportunityAlert) -> Dict[str, Any]:
        self._validate_signal_for_copytrade(alert)

        explanation = (alert.explanation or "").upper()
        if "VENDA" in explanation or "SELL" in explanation:
            side = "SELL"
        elif "COMPRA" in explanation or "BUY" in explanation:
            side = "BUY"
        else:
            raise RuntimeError("Copy trade bloqueado: direcao da ordem nao identificada com seguranca no sinal.")

        payload = {
            "symbol": alert.asset,
            "side": side,
            "risk_percent": self.max_risk_percent,
            "strategy_tag": "zairyx-copytrade-v1",
            "meta": {
                "classification": alert.classification,
                "score": alert.score,
                "sources": alert.sources,
            },
        }

        broker_response = self.adapter.place_order(payload)
        return {
            "success": True,
            "payload": payload,
            "broker_response": broker_response,
        }
