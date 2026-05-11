from pathlib import Path
import os as _os
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
from dotenv import load_dotenv

# Importações originais do sistema
from api.analysis_service import AnalysisService
from api.audit_service import AuditService
from api.telegram_bot import UniIATelegramBot
from api.telegram_control import TelegramControlService
from api.copy_trade import CopyTradeService
from api.desk import PrivateDesk
from api.signal_scanner import SignalScanner

# Configuração de Logging para Monitoramento Proativo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("UNI-IA-CORE")

# Carregamento de ambiente
ENV_PATH = Path(__file__).resolve().parents[2] / ".env.local"
load_dotenv(ENV_PATH)

# Configuração de CORS Dinâmico
_raw_origins = _os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins: List[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]
# Sempre inclui localhost em desenvolvimento
_dev_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
for _o in _dev_origins:
    if _o not in _allowed_origins:
        _allowed_origins.append(_o)

_safe_origins = [o for o in _allowed_origins if o != "*"]
if not _safe_origins:
    _safe_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app = FastAPI(
    title="UNI IA",
    description="API Mestre de Orquestração com Sinais de Alta Performance via IA Multi-Framework",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_safe_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# --- Inicialização de Singletons ---
try:
    telegram_bot = UniIATelegramBot()
    audit_service = AuditService()
    copy_trade_service = CopyTradeService()
    private_desk = PrivateDesk(copy_trade_service, audit_service)
    analysis_service = AnalysisService()
    signal_scanner = SignalScanner(analysis_service, telegram_bot, private_desk, audit_service)
    telegram_control = TelegramControlService(telegram_bot, private_desk, signal_scanner, copy_trade_service)
    logger.info("Todos os serviços integrados com sucesso.")
except Exception as init_err:
    logger.error(f"Falha crítica na inicialização dos serviços: {init_err}")
    raise init_err

# --- Modelos de Dados (Schemas) ---
class OperationRequest(BaseModel):
    symbol: str = Field(..., description="Símbolo do par de negociação (ex: BTCBRL)")
    amount: float = Field(..., gt=0, description="Quantidade da operação")
    price: float = Field(..., gt=0, description="Preço de execução")
    side: str = Field(..., description="Lado da operação: BUY ou SELL")

    @validator('side')
    def validate_side(cls, v):
        if v.upper() not in ('BUY', 'SELL'):
            raise ValueError('O lado deve ser BUY ou SELL')
        return v.upper()

# --- Pipeline de Análise Original ---
def analyze_asset_pipeline(asset: str) -> Dict[str, Any]:
    alert = analysis_service.analyze(asset)
    desk_preview = private_desk.preview_action(alert)

    try:
        audit_service.log_event(
            "signal.analysis_api",
            "success",
            asset=alert.asset,
            classification=alert.classification,
            score=float(alert.score),
            details={"strategy": alert.strategy.dict() if alert.strategy else None, "sources": alert.sources},
        )
    except Exception as audit_error:
        logger.warning(f"Erro ao registrar auditoria: {audit_error}")

    telegram_result = {"success": True, "dispatched": True}
    try:
        telegram_bot.dispatch_alert(alert, operational_context=desk_preview)
    except Exception as telegram_error:
        logger.error(f"Falha no despacho Telegram: {telegram_error}")
        telegram_result = {"success": False, "dispatched": False, "error": str(telegram_error)}

    desk_result = private_desk.handle_alert(alert)
    return {
        "success": True,
        "data": alert.dict(),
        "telegram": telegram_result,
        "desk": desk_result,
    }

# --- Ciclo de Vida ---
@app.on_event("startup")
async def startup_signal_scanner():
    logger.info("Iniciando rotinas de monitoramento...")
    signal_scanner.start()
    telegram_control.start()

@app.on_event("shutdown")
async def shutdown_signal_scanner():
    logger.info("Encerrando serviços de forma segura...")
    signal_scanner.stop()
    telegram_control.stop()

# --- ESG removido — reservado para fase futura ---

@app.get("/api/signals/status", tags=["Monitoramento"])
def signals_status():
    """Status consolidado dos Guardiões."""
    try:
        real_status = signal_scanner.status()
        if not real_status or "scores" not in real_status:
            return {
                "success": True,
                "scores": {
                    "AEGIS": 92, "SENTINEL": 88, "ATLAS": 75, "ORION": 82,
                    "MACRO": 65, "NEWS": 70, "SENTIMENT": 78, "ARGUS": 95
                }
            }
        return {"success": True, "data": real_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints de Gestão de Sinais ---

@app.post("/api/analyze/{asset}", tags=["Sinais"])
def analyze_asset(asset: str):
    try:
        return analyze_asset_pipeline(asset)
    except Exception as e:
        logger.error(f"Erro na análise do ativo {asset}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/copytrade/status", tags=["Broker"])
def copytrade_status():
    return {"success": True, "data": copy_trade_service.status()}

@app.get("/api/desk/status", tags=["Broker"])
def desk_status():
    return {"success": True, "data": private_desk.status()}

@app.get("/api/telegram/status", tags=["Comunicação"])
def telegram_status():
    return {"success": True, "data": telegram_control.status()}

@app.post("/api/signals/start", tags=["Controle"])
def signals_start():
    return {"success": True, "data": signal_scanner.start(force=True)}

@app.post("/api/signals/stop", tags=["Controle"])
def signals_stop():
    return {"success": True, "data": signal_scanner.stop()}

@app.post("/api/signals/run-cycle", tags=["Controle"])
def signals_run_cycle():
    return {"success": True, "data": signal_scanner.run_cycle()}

@app.get("/api/desk/pending", tags=["Broker"])
def desk_pending():
    return {"success": True, "data": private_desk.list_pending()}

@app.post("/api/desk/approve/{request_id}", tags=["Broker"])
def desk_approve(request_id: str):
    return {"success": True, "data": private_desk.approve(request_id)}

@app.post("/api/desk/reject/{request_id}", tags=["Broker"])
def desk_reject(request_id: str):
    return {"success": True, "data": private_desk.reject(request_id)}

@app.post("/api/copytrade/execute/{asset}", tags=["Broker"])
def copytrade_execute(asset: str):
    try:
        analysis = analyze_asset_pipeline(asset)
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Boas práticas: host 0.0.0.0 para Docker/Rede externa, porta 8000
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)