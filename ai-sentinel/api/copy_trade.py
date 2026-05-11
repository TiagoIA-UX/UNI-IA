import os
import json
import hmac
import time
import hashlib
import urllib.parse
from typing import Dict, Any, Optional
import requests
import yfinance as yf
from core.schemas import OpportunityAlert


# ===== ATR-BASED STOP LOSS =====
# Mapeamento de symbols MB/Bybit → yfinance
_SYMBOL_TO_YF: Dict[str, str] = {
    # Mercado Bitcoin (BRL) → yfinance (USD, referência de ATR)
    "BTCBRL":  "BTC-USD",  "BTC":  "BTC-USD",
    "ETHBRL":  "ETH-USD",  "ETH":  "ETH-USD",
    "SOLBRL":  "SOL-USD",  "SOL":  "SOL-USD",
    "XRPBRL":  "XRP-USD",  "XRP":  "XRP-USD",
    "BNBBRL":  "BNB-USD",  "BNB":  "BNB-USD",
    "ADABRL":  "ADA-USD",  "ADA":  "ADA-USD",
    "DOGEBRL": "DOGE-USD", "DOGE": "DOGE-USD",
    "AVAXBRL": "AVAX-USD", "AVAX": "AVAX-USD",
    "LTCBRL":  "LTC-USD",  "LTC":  "LTC-USD",
    "DOTBRL":  "DOT-USD",  "DOT":  "DOT-USD",
    "LINKBRL": "LINK-USD", "LINK": "LINK-USD",
    "MATICBRL":"MATIC-USD","MATIC":"MATIC-USD",
    # Bybit (USDT) — mantido para compatibilidade
    "BTCUSDT": "BTC-USD",
    "ETHUSDT": "ETH-USD",
    "SOLUSDT": "SOL-USD",
    "XRPUSDT": "XRP-USD",
    "BNBUSDT":  "BNB-USD",
    "ADAUSDT":  "ADA-USD",
    "DOGEUSDT": "DOGE-USD",
    "AVAXUSDT": "AVAX-USD",
    "LTCUSDT":  "LTC-USD",
    "DOTUSDT":  "DOT-USD",
}


def _compute_atr_sl(symbol: str, side: str) -> Optional[float]:
    """Calcula o preco de Stop Loss baseado em ATR real.

    Variaveis de ambiente:
    - ATR_SL_ENABLED    (default true)  — desabilita se false
    - ATR_SL_MULTIPLIER (default 1.5)  — fator sobre o ATR
    - ATR_SL_PERIOD     (default 14)   — janela do ATR em barras de 1h

    Retorna o preco do SL ou None se nao for possivel calcular.
    ATR calculado em USD (yfinance); o ratio percentual e aplicado
    ao preco em BRL obtido do ticker MB para calculo proporcional.
    """
    if os.getenv("ATR_SL_ENABLED", "true").lower() != "true":
        return None
    try:
        multiplier = float(os.getenv("ATR_SL_MULTIPLIER", "1.5"))
        period     = int(os.getenv("ATR_SL_PERIOD", "14"))
        yf_sym     = _SYMBOL_TO_YF.get(symbol.upper(), "BTC-USD")

        hist = yf.Ticker(yf_sym).history(period=f"{period + 2}d", interval="1h")
        if hist.empty or len(hist) < period + 1:
            return None

        highs  = hist["High"].tolist()
        lows   = hist["Low"].tolist()
        closes = hist["Close"].tolist()

        trs = [
            max(
                highs[i] - lows[i],
                abs(highs[i]  - closes[i - 1]),
                abs(lows[i]   - closes[i - 1]),
            )
            for i in range(1, len(closes))
        ]
        atr   = sum(trs[-period:]) / period
        price = closes[-1]
        # ratio percentual do SL em relação ao preço USD
        sl_ratio = (atr * multiplier) / price

        # Aplica o ratio ao preço atual do ativo (USD como proxy; para BRL
        # o MercadoBitcoinAdapter substitui pelo preço real em BRL após
        # obter o ticker via API pública).
        sl_usd = price - atr * multiplier if side.upper() in ("BUY", "COMPRA") \
                 else price + atr * multiplier
        return round(sl_usd, 4), round(sl_ratio, 6)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════
#  MERCADO BITCOIN ADAPTER
#  Documentação oficial: https://api.mercadobitcoin.net/api/v4/
#  Autenticação: HMAC-SHA256 conforme doc MB API v4
# ═══════════════════════════════════════════════════════════════
class MercadoBitcoinAdapter:
    """Adapter para a API REST v4 do Mercado Bitcoin.

    Variaveis de ambiente:
    - BROKER_API_KEY         — MB API Key (tapi-id)
    - BROKER_API_SECRET      — MB API Secret (tapi-secret)
    - BROKER_API_BASE_URL    — default https://www.mercadobitcoin.com.br
    - MB_DEFAULT_QTY         — quantidade padrao (default 0.0001 BTC)
    - MB_TRADE_START_HOUR    — hora inicio de operacoes (default 9)
    - MB_TRADE_END_HOUR      — hora fim de operacoes (default 22)
    - MB_ORDER_TIMEOUT_HOURS — timeout de ordens limitadas (default 4)
    - BROKER_TIMEOUT_SECONDS — timeout HTTP (default 10)
    - ATR_SL_ENABLED         — ativa SL baseado em ATR
    """

    MB_API_BASE = "https://api.mercadobitcoin.net"
    MB_TAPI_PATH = "/tapi/v3/"

    def __init__(self):
        self.base_url     = os.getenv("BROKER_API_BASE_URL", "https://www.mercadobitcoin.com.br").rstrip("/")
        self.api_key      = os.getenv("BROKER_API_KEY", "")
        self.api_secret   = os.getenv("BROKER_API_SECRET", "")
        self.default_qty  = os.getenv("MB_DEFAULT_QTY", "0.0001")
        self.timeout      = float(os.getenv("BROKER_TIMEOUT_SECONDS", "10"))
        self.start_hour   = int(os.getenv("MB_TRADE_START_HOUR", "9"))
        self.end_hour     = int(os.getenv("MB_TRADE_END_HOUR", "22"))
        self.order_timeout_hours = int(os.getenv("MB_ORDER_TIMEOUT_HOURS", "4"))

    # ── Validação ─────────────────────────────────────────────────
    def is_ready(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def missing_config(self):
        missing = []
        if not self.api_key:    missing.append("BROKER_API_KEY")
        if not self.api_secret: missing.append("BROKER_API_SECRET")
        return missing

    # ── Janela de horário (09h–22h Brasília) ──────────────────────
    def _dentro_janela(self) -> bool:
        import datetime, zoneinfo
        now = datetime.datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo"))
        return self.start_hour <= now.hour < self.end_hour

    # ── Normalização de símbolo ───────────────────────────────────
    def _normalize_coin(self, symbol: str) -> str:
        """BTCBRL → BTC | ETHBRL → ETH"""
        s = symbol.upper().replace("USDT","").replace("BRL","").replace("/","").replace("_","")
        return s

    # ── Preço atual via API pública MB ───────────────────────────
    def _get_ticker(self, coin: str) -> Optional[Dict[str, Any]]:
        try:
            r = requests.get(
                f"https://www.mercadobitcoin.com.br/api/{coin}/ticker/",
                timeout=self.timeout
            )
            if r.ok:
                return r.json().get("ticker", {})
        except Exception:
            pass
        return None

    # ── Assinatura HMAC-SHA512 (TAPI v3) ─────────────────────────
    def _sign_tapi(self, tapi_method: str, tapi_parameters: str, tapi_nonce: str) -> str:
        """Gera assinatura HMAC-SHA512 conforme doc MB TAPI v3."""
        params_string = self.MB_TAPI_PATH + "?tapi_method=" + tapi_method + "&tapi_nonce=" + tapi_nonce
        if tapi_parameters:
            params_string += "&" + tapi_parameters
        return hmac.new(
            self.api_secret.encode("utf-8"),
            params_string.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()

    def _headers_tapi(self, tapi_method: str, tapi_parameters: str) -> Dict[str, str]:
        tapi_nonce = str(int(time.time() * 1000))
        signature  = self._sign_tapi(tapi_method, tapi_parameters, tapi_nonce)
        return {
            "Content-Type":  "application/x-www-form-urlencoded",
            "TAPI-ID":       self.api_key,
            "TAPI-MAC":      signature,
            "TAPI-NONCE":    tapi_nonce,
        }

    # ── Chamada TAPI v3 ──────────────────────────────────────────
    def _tapi_call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params["tapi_method"] = method
        params["tapi_nonce"]  = str(int(time.time() * 1000))
        body                  = urllib.parse.urlencode(params)

        headers = self._headers_tapi(method, urllib.parse.urlencode(
            {k: v for k, v in params.items() if k not in ("tapi_method", "tapi_nonce")}
        ))
        r = requests.post(
            self.MB_API_BASE + self.MB_TAPI_PATH,
            headers=headers,
            data=body,
            timeout=self.timeout,
        )
        if not r.ok:
            raise RuntimeError(f"MB TAPI HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        if data.get("status_code") not in (100, 200):
            raise RuntimeError(f"MB TAPI erro: {data.get('status_code')} - {data.get('error_message','')}")
        return data.get("response_data", {})

    # ── Colocar ordem ─────────────────────────────────────────────
    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError(
                "Mercado Bitcoin não configurado. "
                "Defina BROKER_API_KEY e BROKER_API_SECRET no .env.local."
            )

        if not self._dentro_janela():
            raise RuntimeError(
                f"Operação fora da janela permitida ({self.start_hour}h–{self.end_hour}h, "
                "horário de Brasília). Ajuste MB_TRADE_START_HOUR / MB_TRADE_END_HOUR."
            )

        raw_symbol = str(payload.get("symbol", "BTCBRL"))
        coin       = self._normalize_coin(raw_symbol)
        side       = str(payload.get("side", "BUY")).upper()
        qty        = str(payload.get("qty", self.default_qty))

        # Preço atual em BRL
        ticker     = self._get_ticker(coin)
        if not ticker:
            raise RuntimeError(f"Não foi possível obter preço atual de {coin} no Mercado Bitcoin.")
        price_brl  = float(ticker.get("last", 0))
        if price_brl <= 0:
            raise RuntimeError(f"Preço inválido recebido para {coin}: {price_brl}")

        # ATR Stop Loss (ratio calculado em USD, aplicado ao preço BRL)
        sl_price_brl = None
        atr_result   = _compute_atr_sl(raw_symbol, side)
        if atr_result and isinstance(atr_result, tuple):
            _, sl_ratio = atr_result
            if side == "BUY":
                sl_price_brl = round(price_brl * (1 - sl_ratio), 2)
            else:
                sl_price_brl = round(price_brl * (1 + sl_ratio), 2)

        # Monta parâmetros da ordem (TAPI v3 — place_buy_order / place_sell_order)
        tapi_method = "place_buy_order" if side == "BUY" else "place_sell_order"
        tapi_params: Dict[str, Any] = {
            "coin_pair":  "BRL" + coin,
            "quantity":   qty,
            "limit_price": str(round(
                price_brl * 1.003 if side == "BUY" else price_brl * 0.997, 2
            )),
        }

        response = self._tapi_call(tapi_method, tapi_params)

        result = {
            "success":       True,
            "broker":        "mercadobitcoin",
            "coin":          coin,
            "side":          side,
            "qty":           qty,
            "price_brl":     price_brl,
            "sl_price_brl":  sl_price_brl,
            "order_response": response,
            "meta":          payload.get("meta", {}),
        }
        return result

    # ── Consultar ordem ──────────────────────────────────────────
    def get_order(self, coin: str, order_id: str) -> Dict[str, Any]:
        coin = self._normalize_coin(coin)
        return self._tapi_call("get_order", {
            "coin_pair": "BRL" + coin,
            "order_id":  order_id,
        })

    # ── Cancelar ordem ───────────────────────────────────────────
    def cancel_order(self, coin: str, order_id: str) -> Dict[str, Any]:
        coin = self._normalize_coin(coin)
        return self._tapi_call("cancel_order", {
            "coin_pair": "BRL" + coin,
            "order_id":  order_id,
        })

    # ── Saldo da conta ───────────────────────────────────────────
    def get_account_info(self) -> Dict[str, Any]:
        return self._tapi_call("get_account_info", {})


# ═══════════════════════════════════════════════════════════════
#  ADAPTER GENÉRICO (fallback)
# ═══════════════════════════════════════════════════════════════
class GenericBrokerAdapter:
    """Adapter HTTP generico para broker/exchange personalizado."""

    def __init__(self):
        self.base_url    = os.getenv("BROKER_API_BASE_URL", "").rstrip("/")
        self.api_key     = os.getenv("BROKER_API_KEY", "")
        self.account_id  = os.getenv("BROKER_ACCOUNT_ID", "")
        self.timeout_sec = float(os.getenv("BROKER_TIMEOUT_SECONDS", "10"))

    def is_ready(self) -> bool:
        return bool(self.base_url and self.api_key and self.account_id)

    def missing_config(self):
        missing = []
        if not self.base_url:   missing.append("BROKER_API_BASE_URL")
        if not self.api_key:    missing.append("BROKER_API_KEY")
        if not self.account_id: missing.append("BROKER_ACCOUNT_ID")
        return missing

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
            "X-Account-Id":  self.account_id,
        }

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError(
                "Broker genérico não configurado. "
                "Defina BROKER_API_BASE_URL, BROKER_API_KEY e BROKER_ACCOUNT_ID."
            )
        r = requests.post(
            f"{self.base_url}/orders",
            headers=self._headers(),
            json=payload,
            timeout=self.timeout_sec,
        )
        if not r.ok:
            raise RuntimeError(f"Erro HTTP {r.status_code}: {r.text[:300]}")
        return r.json()


# ═══════════════════════════════════════════════════════════════
#  BYBIT ADAPTER (secundário / análise)
# ═══════════════════════════════════════════════════════════════
class BybitBrokerAdapter:
    """Adapter Bybit API V5 (REST). Usado apenas como secundário
    para dados de mercado ou paper trading enquanto BROKER_PROVIDER != bybit."""

    def __init__(self):
        self.base_url     = os.getenv("BYBIT_API_BASE_URL", "https://api.bybit.com").rstrip("/")
        self.api_key      = os.getenv("BYBIT_API_KEY", os.getenv("BROKER_API_KEY", ""))
        self.api_secret   = os.getenv("BYBIT_API_SECRET", os.getenv("BROKER_API_SECRET", ""))
        self.timeout_sec  = float(os.getenv("BROKER_TIMEOUT_SECONDS", "10"))
        self.recv_window  = os.getenv("BYBIT_RECV_WINDOW", "5000")
        self.category     = os.getenv("BYBIT_CATEGORY", "linear")
        self.default_qty  = os.getenv("BYBIT_DEFAULT_QTY", "0.001")

    def is_ready(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def missing_config(self):
        missing = []
        if not self.api_key:    missing.append("BYBIT_API_KEY")
        if not self.api_secret: missing.append("BYBIT_API_SECRET")
        return missing

    def _sign(self, timestamp: str, payload_json: str) -> str:
        raw = f"{timestamp}{self.api_key}{self.recv_window}{payload_json}"
        return hmac.new(self.api_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()

    def _normalize_symbol(self, symbol: str) -> str:
        return symbol.replace("/","").replace("_","").replace("BRL","USDT").upper()

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError("Bybit não configurado. Defina BYBIT_API_KEY e BYBIT_API_SECRET.")

        timestamp    = str(int(time.time() * 1000))
        order_symbol = self._normalize_symbol(str(payload.get("symbol", "")))
        side         = str(payload.get("side", "BUY")).upper()
        qty          = str(payload.get("qty", self.default_qty))

        bybit_payload = {
            "category":     self.category,
            "symbol":       order_symbol,
            "side":         "Buy" if side == "BUY" else "Sell",
            "orderType":    "Market",
            "qty":          qty,
            "timeInForce":  "IOC",
            "orderLinkId":  f"uniia-{int(time.time())}",
        }
        atr_result = _compute_atr_sl(order_symbol, side)
        if atr_result and isinstance(atr_result, tuple):
            sl_price, _ = atr_result
            bybit_payload["stopLoss"]    = str(round(sl_price, 2))
            bybit_payload["slTriggerBy"] = "MarkPrice"
            bybit_payload["slOrderType"] = "Market"

        payload_json = json.dumps(bybit_payload, separators=(",", ":"))
        sign         = self._sign(timestamp, payload_json)

        headers = {
            "X-BAPI-API-KEY":     self.api_key,
            "X-BAPI-SIGN":        sign,
            "X-BAPI-TIMESTAMP":   timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type":       "application/json",
        }
        r = requests.post(
            f"{self.base_url}/v5/order/create",
            headers=headers, data=payload_json, timeout=self.timeout_sec,
        )
        if not r.ok:
            raise RuntimeError(f"Bybit HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        if data.get("retCode") != 0:
            raise RuntimeError(f"Bybit recusou: {data.get('retCode')} - {data.get('retMsg')}")
        return data


# ═══════════════════════════════════════════════════════════════
#  COPY TRADE SERVICE
# ═══════════════════════════════════════════════════════════════
class CopyTradeService:
    """Orquestra a execução automática de ordens a partir de sinais dos agentes.

    BROKER_PROVIDER=mercadobitcoin → usa MercadoBitcoinAdapter (padrão)
    BROKER_PROVIDER=bybit          → usa BybitBrokerAdapter
    BROKER_PROVIDER=generic        → usa GenericBrokerAdapter
    """

    def __init__(self):
        self.enabled        = os.getenv("COPY_TRADE_ENABLED", "false").lower() == "true"
        self.min_confidence = int(os.getenv("COPY_TRADE_MIN_CONFIDENCE", "75"))
        self.max_risk_pct   = float(os.getenv("COPY_TRADE_MAX_RISK_PERCENT", "1.0"))
        self.provider       = os.getenv("BROKER_PROVIDER", "mercadobitcoin").lower()
        self.adapter        = self._build_adapter()

    def _build_adapter(self):
        if self.provider == "mercadobitcoin":
            return MercadoBitcoinAdapter()
        if self.provider == "bybit":
            return BybitBrokerAdapter()
        return GenericBrokerAdapter()

    def status(self) -> Dict[str, Any]:
        missing = self.adapter.missing_config()
        return {
            "enabled":        self.enabled,
            "provider":       self.provider,
            "broker_ready":   len(missing) == 0,
            "missing_config": missing,
            "min_confidence": self.min_confidence,
            "max_risk_percent": self.max_risk_pct,
        }

    def _validate_signal_for_copytrade(self, alert: OpportunityAlert):
        if not self.enabled:
            raise RuntimeError("Copy trade desativado (COPY_TRADE_ENABLED=false).")
        if not self.adapter.is_ready():
            raise RuntimeError(
                f"Copy trade bloqueado: broker '{self.provider}' não configurado. "
                f"Verifique: {self.adapter.missing_config()}"
            )
        if alert.classification != "OPORTUNIDADE":
            raise RuntimeError(
                f"Copy trade bloqueado: sinal '{alert.classification}' não é OPORTUNIDADE."
            )
        if alert.score < self.min_confidence:
            raise RuntimeError(
                f"Copy trade bloqueado: score {alert.score} < mínimo {self.min_confidence}."
            )

    def execute_from_alert(self, alert: OpportunityAlert) -> Dict[str, Any]:
        self._validate_signal_for_copytrade(alert)

        strategy_direction = (
            (alert.strategy.direction if alert.strategy else "") or ""
        ).lower()
        explanation = (alert.explanation or "").upper()

        if strategy_direction == "short" or "VENDA" in explanation or "SELL" in explanation:
            side = "SELL"
        elif strategy_direction == "long" or "COMPRA" in explanation or "BUY" in explanation:
            side = "BUY"
        else:
            raise RuntimeError(
                "Copy trade bloqueado: direção da ordem não identificada com segurança no sinal."
            )

        payload = {
            "symbol":       alert.asset,
            "side":         side,
            "risk_percent": self.max_risk_pct,
            "strategy_tag": "uni-ia-copytrade-v1",
            "meta": {
                "classification":     alert.classification,
                "score":              alert.score,
                "sources":            alert.sources,
                "strategy_mode":      alert.strategy.mode if alert.strategy else None,
                "strategy_timeframe": alert.strategy.timeframe if alert.strategy else None,
            },
        }

        broker_response = self.adapter.place_order(payload)
        return {
            "success":         True,
            "payload":         payload,
            "broker_response": broker_response,
        }

    def execute_manual_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: Optional[str] = None,
        risk_percent: Optional[float] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Envia ordem ao broker sem exigir COPY_TRADE_ENABLED (uso pela mesa / UI manual)."""
        if not self.adapter.is_ready():
            raise RuntimeError(
                f"Broker '{self.provider}' nao configurado. Faltando: {self.adapter.missing_config()}"
            )
        side_raw = (side or "").strip().upper()
        if side_raw in ("COMPRA", "BUY"):
            side_u = "BUY"
        elif side_raw in ("VENDA", "SELL"):
            side_u = "SELL"
        else:
            raise RuntimeError("Lado invalido: use BUY ou SELL.")

        qty = quantity
        if not qty:
            dq = getattr(self.adapter, "default_qty", None)
            if dq is None:
                dq = (
                    os.getenv("MB_DEFAULT_QTY", "0.0001")
                    if self.provider == "mercadobitcoin"
                    else os.getenv("BYBIT_DEFAULT_QTY", "0.001")
                )
            qty = str(dq)

        payload: Dict[str, Any] = {
            "symbol": symbol,
            "side":   side_u,
            "qty":    qty,
            "meta":   meta or {},
        }
        if risk_percent is not None:
            payload["risk_percent"] = risk_percent

        broker_response = self.adapter.place_order(payload)
        return {
            "success":         True,
            "payload":         payload,
            "broker_response": broker_response,
        }
