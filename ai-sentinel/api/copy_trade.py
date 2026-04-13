import os
import json
import hmac
import time
import hashlib
from typing import Dict, Any
import requests
from ..core.schemas import OpportunityAlert


class GenericBrokerAdapter:
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
        self.provider = os.getenv("BROKER_PROVIDER", "bybit").lower()
        self.adapter = self._build_adapter()

    def _build_adapter(self):
        if self.provider == "bybit":
            return BybitBrokerAdapter()
        return GenericBrokerAdapter()

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
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
            "strategy_tag": "uni-ia-copytrade-v1",
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


class BybitBrokerAdapter:
    """Adapter Bybit API V5 (REST).

    Requer:
    - BROKER_API_KEY
    - BROKER_API_SECRET
    Opcional:
    - BROKER_API_BASE_URL (default https://api.bybit.com)
    - BYBIT_CATEGORY (default linear)
    - BYBIT_DEFAULT_QTY (default 0.001)
    - BROKER_TIMEOUT_SECONDS (default 10)
    """

    def __init__(self):
        self.base_url = os.getenv("BROKER_API_BASE_URL", "https://api.bybit.com").rstrip("/")
        self.api_key = os.getenv("BROKER_API_KEY", "")
        self.api_secret = os.getenv("BROKER_API_SECRET", "")
        self.timeout_seconds = float(os.getenv("BROKER_TIMEOUT_SECONDS", "10"))
        self.recv_window = os.getenv("BYBIT_RECV_WINDOW", "5000")
        self.category = os.getenv("BYBIT_CATEGORY", "linear")
        self.default_qty = os.getenv("BYBIT_DEFAULT_QTY", "0.001")

    def is_ready(self) -> bool:
        return bool(self.base_url and self.api_key and self.api_secret)

    def _sign(self, timestamp: str, payload_json: str) -> str:
        raw = f"{timestamp}{self.api_key}{self.recv_window}{payload_json}"
        return hmac.new(self.api_secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()

    def _normalize_symbol(self, symbol: str) -> str:
        return symbol.replace("/", "").replace("_", "").upper()

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError("Bybit nao configurado. Defina BROKER_API_KEY e BROKER_API_SECRET.")

        timestamp = str(int(time.time() * 1000))
        order_symbol = self._normalize_symbol(str(payload.get("symbol", "")))
        side = str(payload.get("side", "BUY")).upper()
        qty = str(payload.get("qty", self.default_qty))
        bybit_payload = {
            "category": self.category,
            "symbol": order_symbol,
            "side": "Buy" if side == "BUY" else "Sell",
            "orderType": "Market",
            "qty": qty,
            "timeInForce": "IOC",
            "orderLinkId": f"uniia-{int(time.time())}",
        }
        payload_json = json.dumps(bybit_payload, separators=(",", ":"))
        sign = self._sign(timestamp, payload_json)

        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": sign,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type": "application/json",
        }

        response = requests.post(
            f"{self.base_url}/v5/order/create",
            headers=headers,
            data=payload_json,
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(f"Erro Bybit HTTP {response.status_code}: {response.text[:300]}")

        data = response.json()
        if data.get("retCode") != 0:
            raise RuntimeError(f"Bybit recusou ordem: {data.get('retCode')} - {data.get('retMsg')}")

        return data
