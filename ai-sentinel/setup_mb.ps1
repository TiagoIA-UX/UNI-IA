# ============================================================
#  UNI IA — Integração Mercado Bitcoin
#  Execute com: pwsh -ExecutionPolicy Bypass -File .\setup_mb.ps1
#  ou cole direto no PowerShell 7+ com venv ativo
# ============================================================

$ROOT      = "E:\UNI.IA\ai-sentinel"
$ADAPTERS  = "$ROOT\adapters"
$API       = "$ROOT\api"
$ENV_FILE  = "$ROOT\.env.local"
$PASS      = "[OK]"
$FAIL      = "[ERRO]"
$WARN      = "[AVISO]"

function Write-Header($txt) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  $txt" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

# ─── 1. BACKUP ────────────────────────────────────────────────────────────────
Write-Header "1. BACKUP DOS ARQUIVOS ORIGINAIS"

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

if (Test-Path "$ADAPTERS\mercadobitcoin_adapter.py") {
    Copy-Item "$ADAPTERS\mercadobitcoin_adapter.py" `
              "$ADAPTERS\mercadobitcoin_adapter.py.bak_$timestamp"
    Write-Host "$PASS Backup do adapter criado" -ForegroundColor Green
}

if (Test-Path "$API\copy_trade.py") {
    Copy-Item "$API\copy_trade.py" "$API\copy_trade.py.bak_$timestamp"
    Write-Host "$PASS Backup do copy_trade.py criado" -ForegroundColor Green
}

if (Test-Path $ENV_FILE) {
    Copy-Item $ENV_FILE "$ENV_FILE.bak_$timestamp"
    Write-Host "$PASS Backup do .env.local criado" -ForegroundColor Green
} else {
    Write-Host "$WARN .env.local não encontrado em $ENV_FILE" -ForegroundColor Yellow
}

# ─── 2. ADAPTER MERCADO BITCOIN ───────────────────────────────────────────────
Write-Header "2. GRAVANDO mercadobitcoin_adapter.py"

$adapterCode = @'
"""
Adapter Mercado Bitcoin via CCXT — UNI IA
==========================================
Substitui o adapter Bybit quando BROKER_PROVIDER=mercadobitcoin

Variaveis de ambiente necessarias:
  BROKER_API_KEY          -> API Key gerada no painel MB
  BROKER_API_SECRET       -> Secret gerado no painel MB
  MB_DEFAULT_QTY          -> Quantidade padrao (ex: 0.0001 BTC)
  MB_TRADE_START_HOUR     -> Hora de inicio da janela (ex: 9)
  MB_TRADE_END_HOUR       -> Hora limite para NOVAS entradas (ex: 22)
  MB_ORDER_TIMEOUT_HOURS  -> Horas maximas que uma posicao fica aberta (ex: 4)
  ATR_SL_ENABLED          -> true/false
  ATR_SL_MULTIPLIER       -> Multiplicador ATR (ex: 1.5)
  ATR_SL_PERIOD           -> Periodo ATR em barras 1h (ex: 14)

Mandato Zero Bug:
  - Falha de API -> RuntimeError com mensagem explicita (sem fallback silencioso)
  - Fora da janela de horario -> bloqueio com motivo claro
  - Credenciais ausentes -> bloqueio antes de qualquer chamada de rede
"""

import os
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import ccxt
import yfinance as yf

logger = logging.getLogger(__name__)

_SYMBOL_TO_MB: Dict[str, str] = {
    "BTCUSDT":  "BTC/BRL",
    "ETHUSDT":  "ETH/BRL",
    "SOLUSDT":  "SOL/BRL",
    "XRPUSDT":  "XRP/BRL",
    "BNBUSDT":  "BNB/BRL",
    "ADAUSDT":  "ADA/BRL",
    "DOGEUSDT": "DOGE/BRL",
    "LTCUSDT":  "LTC/BRL",
    "LINKUSDT": "LINK/BRL",
    "UNIUSDT":  "UNI/BRL",
}

_BYBIT_TO_YF: Dict[str, str] = {
    "BTCUSDT":  "BTC-USD",
    "ETHUSDT":  "ETH-USD",
    "SOLUSDT":  "SOL-USD",
    "XRPUSDT":  "XRP-USD",
    "BNBUSDT":  "BNB-USD",
    "ADAUSDT":  "ADA-USD",
    "DOGEUSDT": "DOGE-USD",
    "LTCUSDT":  "LTC-USD",
}


def _compute_atr_sl(symbol: str, side: str) -> Optional[float]:
    if os.getenv("ATR_SL_ENABLED", "true").lower() != "true":
        return None
    try:
        multiplier = float(os.getenv("ATR_SL_MULTIPLIER", "1.5"))
        period     = int(os.getenv("ATR_SL_PERIOD", "14"))
        yf_sym     = _BYBIT_TO_YF.get(symbol.upper(), symbol.replace("USDT", "-USD"))
        hist = yf.Ticker(yf_sym).history(period=f"{period + 2}d", interval="1h")
        if hist.empty or len(hist) < period + 1:
            return None
        highs  = hist["High"].tolist()
        lows   = hist["Low"].tolist()
        closes = hist["Close"].tolist()
        trs = [
            max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
            for i in range(1, len(closes))
        ]
        atr   = sum(trs[-period:]) / period
        price = closes[-1]
        sl    = price - atr * multiplier if side.upper() == "BUY" else price + atr * multiplier
        logger.info(f"[MB_ATR] {symbol} {side} | preco={price:.4f} ATR={atr:.4f} SL={sl:.4f}")
        return round(sl, 4)
    except Exception as exc:
        logger.warning(f"[MB_ATR] Falha ao calcular ATR para {symbol}: {exc}")
        return None


class TradeWindowGuard:
    """Controla a janela de horario de operacao.

    - Novas entradas so entre MB_TRADE_START_HOUR e MB_TRADE_END_HOUR
    - Posicoes abertas monitoradas por MB_ORDER_TIMEOUT_HOURS
    - MB opera 24/7 — janela e decisao operacional, nao tecnica
    Recomendacao: 9h-22h (horario de Brasilia) para evitar baixa liquidez.
    """

    def __init__(self):
        self.start_hour    = int(os.getenv("MB_TRADE_START_HOUR", "9"))
        self.end_hour      = int(os.getenv("MB_TRADE_END_HOUR", "22"))
        self.timeout_hours = float(os.getenv("MB_ORDER_TIMEOUT_HOURS", "4"))

    def is_entry_allowed(self) -> tuple:
        hour = datetime.now().hour
        if hour < self.start_hour:
            return False, f"Fora da janela: mercado abre as {self.start_hour}h (agora {hour}h)"
        if hour >= self.end_hour:
            return False, f"Fora da janela: novas entradas encerradas as {self.end_hour}h (agora {hour}h)"
        return True, "ok"

    def is_position_expired(self, opened_at_ts: float) -> tuple:
        elapsed_hours = (time.time() - opened_at_ts) / 3600
        if elapsed_hours >= self.timeout_hours:
            return True, f"Posicao expirada apos {elapsed_hours:.1f}h (limite: {self.timeout_hours}h)"
        return False, f"Posicao ativa ha {elapsed_hours:.1f}h"

    def summary(self) -> Dict[str, Any]:
        allowed, reason = self.is_entry_allowed()
        return {
            "entry_allowed":      allowed,
            "reason":             reason,
            "window":             f"{self.start_hour}h-{self.end_hour}h",
            "max_position_hours": self.timeout_hours,
            "current_hour":       datetime.now().hour,
        }


class MercadoBitcoinAdapter:
    """Adapter Mercado Bitcoin via CCXT.
    Interface identica ao BybitBrokerAdapter — drop-in replacement.
    """

    def __init__(self):
        self.api_key     = os.getenv("BROKER_API_KEY", "")
        self.api_secret  = os.getenv("BROKER_API_SECRET", "")
        self.default_qty = float(os.getenv("MB_DEFAULT_QTY", "0.0001"))
        self.timeout_sec = float(os.getenv("BROKER_TIMEOUT_SECONDS", "10"))
        self.window      = TradeWindowGuard()
        self._open_orders: Dict[str, float] = {}
        self._exchange: Optional[ccxt.mercadobitcoin] = None
        if self.is_ready():
            self._exchange = ccxt.mercadobitcoin({
                "apiKey":          self.api_key,
                "secret":          self.api_secret,
                "enableRateLimit": True,
                "timeout":         int(self.timeout_sec * 1000),
            })

    def is_ready(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def missing_config(self) -> list:
        missing = []
        if not self.api_key:    missing.append("BROKER_API_KEY")
        if not self.api_secret: missing.append("BROKER_API_SECRET")
        return missing

    def _resolve_symbol(self, raw_symbol: str) -> str:
        normalized = raw_symbol.upper().replace("/", "").replace("_", "")
        if normalized in _SYMBOL_TO_MB:
            return _SYMBOL_TO_MB[normalized]
        if normalized.endswith("BRL"):
            return f"{normalized[:-3]}/BRL"
        raise RuntimeError(
            f"Simbolo '{raw_symbol}' nao mapeado para o Mercado Bitcoin. "
            f"Suportados: {list(_SYMBOL_TO_MB.keys())}"
        )

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError(
                "Mercado Bitcoin nao configurado. "
                "Defina BROKER_API_KEY e BROKER_API_SECRET no .env.local"
            )
        allowed, reason = self.window.is_entry_allowed()
        if not allowed:
            raise RuntimeError(f"[MB_WINDOW] Entrada bloqueada: {reason}")

        raw_symbol = str(payload.get("symbol", "BTCUSDT"))
        mb_symbol  = self._resolve_symbol(raw_symbol)
        side       = str(payload.get("side", "BUY")).upper()
        qty        = float(payload.get("qty", self.default_qty))
        atr_sl     = _compute_atr_sl(raw_symbol, side)

        if atr_sl:
            logger.info(f"[MB_ORDER] ATR SL ref: {atr_sl:.4f} USD (gerencie via ARGUS)")

        logger.info(f"[MB_ORDER] Enviando: {mb_symbol} {side} qty={qty}")
        try:
            response = self._exchange.create_order(
                symbol=mb_symbol, type="market",
                side="buy" if side == "BUY" else "sell", amount=qty,
            )
        except ccxt.AuthenticationError as exc:
            raise RuntimeError(f"[MB_AUTH] Credenciais invalidas: {exc}. Regenere a API Key no MB.") from exc
        except ccxt.InsufficientFunds as exc:
            raise RuntimeError(f"[MB_FUNDS] Saldo insuficiente para {mb_symbol} qty={qty}: {exc}") from exc
        except ccxt.NetworkError as exc:
            raise RuntimeError(f"[MB_NETWORK] Falha de rede ao conectar ao MB: {exc}") from exc
        except ccxt.ExchangeError as exc:
            raise RuntimeError(f"[MB_EXCHANGE] Erro da exchange: {exc}") from exc

        order_id = str(response.get("id", f"mb-{int(time.time())}"))
        self._open_orders[order_id] = time.time()
        logger.info(f"[MB_ORDER] Criada: id={order_id} {mb_symbol} {side}")

        return {
            "broker":       "mercadobitcoin",
            "order_id":     order_id,
            "symbol":       mb_symbol,
            "symbol_raw":   raw_symbol,
            "side":         side,
            "qty":          qty,
            "atr_sl_ref":   atr_sl,
            "window":       self.window.summary(),
            "opened_at":    datetime.now(timezone.utc).isoformat(),
            "raw_response": response,
        }

    def check_open_positions_timeout(self) -> list:
        expired = []
        for order_id, opened_ts in list(self._open_orders.items()):
            is_expired, reason = self.window.is_position_expired(opened_ts)
            if is_expired:
                expired.append({"order_id": order_id, "reason": reason})
                logger.warning(f"[MB_TIMEOUT] {reason} — order_id={order_id}")
        return expired

    def get_window_status(self) -> Dict[str, Any]:
        return self.window.summary()
'@

Set-Content -Path "$ADAPTERS\mercadobitcoin_adapter.py" -Value $adapterCode -Encoding UTF8
Write-Host "$PASS mercadobitcoin_adapter.py gravado em $ADAPTERS" -ForegroundColor Green

# ─── 3. PATCH copy_trade.py ───────────────────────────────────────────────────
Write-Header "3. APLICANDO PATCH NO copy_trade.py"

$copyTrade = Get-Content "$API\copy_trade.py" -Raw

# Verifica se import ja existe
if ($copyTrade -match "mercadobitcoin_adapter") {
    Write-Host "$WARN Import do MercadoBitcoinAdapter ja existe — pulando import" -ForegroundColor Yellow
} else {
    $copyTrade = $copyTrade -replace `
        "from core\.schemas import OpportunityAlert", `
        "from core.schemas import OpportunityAlert`nfrom adapters.mercadobitcoin_adapter import MercadoBitcoinAdapter"
    Write-Host "$PASS Import adicionado" -ForegroundColor Green
}

# Verifica se roteamento ja existe
if ($copyTrade -match '"mercadobitcoin"') {
    Write-Host "$WARN Roteamento mercadobitcoin ja existe — pulando _build_adapter" -ForegroundColor Yellow
} else {
    $copyTrade = $copyTrade -replace `
        "def _build_adapter\(self\):\s*\r?\n\s*if self\.provider == ""bybit"":\s*\r?\n\s*return BybitBrokerAdapter\(\)\s*\r?\n\s*return GenericBrokerAdapter\(\)", `
        "def _build_adapter(self):`n        if self.provider == ""bybit"":`n            return BybitBrokerAdapter()`n        if self.provider == ""mercadobitcoin"":`n            return MercadoBitcoinAdapter()`n        return GenericBrokerAdapter()"
    Write-Host "$PASS Roteamento mercadobitcoin adicionado ao _build_adapter" -ForegroundColor Green
}

Set-Content -Path "$API\copy_trade.py" -Value $copyTrade -Encoding UTF8
Write-Host "$PASS copy_trade.py salvo" -ForegroundColor Green

# ─── 4. .env.local ────────────────────────────────────────────────────────────
Write-Header "4. ATUALIZANDO .env.local"

$envVars = @"

# === BROKER: MERCADO BITCOIN (adicionado pelo setup_mb.ps1) ===
# Troque para "bybit" se quiser voltar ao paper na Bybit
BROKER_PROVIDER=mercadobitcoin
MB_DEFAULT_QTY=0.0001
MB_TRADE_START_HOUR=9
MB_TRADE_END_HOUR=22
MB_ORDER_TIMEOUT_HOURS=4

# IMPORTANTE: substitua os valores abaixo pelas suas chaves reais do MB
# Painel MB: Conta -> Seguranca -> API -> Criar nova chave
# Permissoes: marque APENAS Trade e Consultar (NUNCA Saque)
# BROKER_API_KEY=SUA_CHAVE_AQUI
# BROKER_API_SECRET=SEU_SECRET_AQUI
"@

# Verifica se ja tem MB configurado
if (Test-Path $ENV_FILE) {
    $envContent = Get-Content $ENV_FILE -Raw
    if ($envContent -match "MB_DEFAULT_QTY") {
        Write-Host "$WARN Variaveis MB ja existem no .env.local — nao duplicando" -ForegroundColor Yellow
    } else {
        Add-Content -Path $ENV_FILE -Value $envVars -Encoding UTF8
        Write-Host "$PASS Variaveis MB adicionadas ao .env.local" -ForegroundColor Green
    }
} else {
    Set-Content -Path $ENV_FILE -Value $envVars -Encoding UTF8
    Write-Host "$WARN .env.local criado do zero (confira as outras variaveis)" -ForegroundColor Yellow
}

# ─── 5. VALIDACAO ─────────────────────────────────────────────────────────────
Write-Header "5. VALIDACAO"

# Verifica adapter
if (Test-Path "$ADAPTERS\mercadobitcoin_adapter.py") {
    $lines = (Get-Content "$ADAPTERS\mercadobitcoin_adapter.py").Count
    Write-Host "$PASS Adapter gravado ($lines linhas)" -ForegroundColor Green
} else {
    Write-Host "$FAIL Adapter nao encontrado" -ForegroundColor Red
}

# Verifica import no copy_trade
$check = Select-String -Path "$API\copy_trade.py" -Pattern "MercadoBitcoinAdapter"
if ($check) {
    Write-Host "$PASS Import MercadoBitcoinAdapter confirmado no copy_trade.py" -ForegroundColor Green
} else {
    Write-Host "$FAIL Import NAO encontrado — aplique manualmente" -ForegroundColor Red
    Write-Host "   Adicione apos 'from core.schemas import OpportunityAlert':" -ForegroundColor Yellow
    Write-Host "   from adapters.mercadobitcoin_adapter import MercadoBitcoinAdapter" -ForegroundColor Yellow
}

# Verifica roteamento
$checkRoute = Select-String -Path "$API\copy_trade.py" -Pattern '"mercadobitcoin"'
if ($checkRoute) {
    Write-Host "$PASS Roteamento mercadobitcoin confirmado no _build_adapter" -ForegroundColor Green
} else {
    Write-Host "$FAIL Roteamento NAO encontrado — aplique manualmente (veja PATCH_copy_trade.py)" -ForegroundColor Red
}

# Verifica ccxt
try {
    $ccxtVersion = python -c "import ccxt; print(ccxt.__version__)" 2>&1
    Write-Host "$PASS ccxt $ccxtVersion instalado" -ForegroundColor Green
} catch {
    Write-Host "$FAIL ccxt nao instalado — rode: pip install ccxt" -ForegroundColor Red
}

# ─── 6. PROXIMO PASSO ─────────────────────────────────────────────────────────
Write-Header "PROXIMO PASSO"
Write-Host ""
Write-Host "  1. Abra o .env.local e coloque suas chaves reais do MB:" -ForegroundColor White
Write-Host "     BROKER_API_KEY=sua_chave" -ForegroundColor Cyan
Write-Host "     BROKER_API_SECRET=seu_secret" -ForegroundColor Cyan
Write-Host ""
Write-Host "  2. Mantenha DESK_MODE=paper ate validar" -ForegroundColor White
Write-Host ""
Write-Host "  3. Suba o backend:" -ForegroundColor White
Write-Host "     cd $ROOT" -ForegroundColor Cyan
Write-Host "     python run_local_api.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Teste o status:" -ForegroundColor White
Write-Host '     Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/desk/status"' -ForegroundColor Cyan
Write-Host ""
Write-Host "  Esperado: provider=mercadobitcoin, broker_ready=false (ate colocar as chaves)" -ForegroundColor Yellow
Write-Host ""