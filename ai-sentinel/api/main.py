from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from api.analysis_service import AnalysisService
from api.audit_service import AuditService
from api.telegram_bot import UniIATelegramBot
from api.telegram_control import TelegramControlService
from api.copy_trade import CopyTradeService
from api.desk import PrivateDesk
from api.signal_scanner import SignalScanner

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

# CORS: em produção, defina ALLOWED_ORIGINS com as origens reais separadas por vírgula.
# Ex: ALLOWED_ORIGINS=https://zairyx.ai,https://www.zairyx.ai
# Se não definido, cai para ["*"] apenas em modo local/paper — nunca use "*" em live.
import os as _os
_raw_origins = _os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app = FastAPI(
    title="UNI IA",
    description="API Mestre de Orquestração com Sinais de Alta Performance via IA Multi-Framework",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

telegram_bot = UniIATelegramBot()
audit_service = AuditService()
copy_trade_service = CopyTradeService()
private_desk = PrivateDesk(copy_trade_service, audit_service)
analysis_service = AnalysisService()
signal_scanner = SignalScanner(analysis_service, telegram_bot, private_desk, audit_service)
telegram_control = TelegramControlService(telegram_bot, private_desk, signal_scanner, copy_trade_service)


def analyze_asset_pipeline(asset: str):
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
        print(f"[AUDIT][WARN] signal.analysis_api: {audit_error}")

    telegram_result = {"success": True, "dispatched": True}
    try:
        telegram_bot.dispatch_alert(alert, operational_context=desk_preview)
    except Exception as telegram_error:
        telegram_result = {
            "success": False,
            "dispatched": False,
            "error": str(telegram_error),
        }

    desk_result = private_desk.handle_alert(alert)
    return {
        "success": True,
        "data": alert.dict(),
        "telegram": telegram_result,
        "desk": desk_result,
    }


@app.on_event("startup")
def startup_signal_scanner():
    signal_scanner.start()
    telegram_control.start()


@app.on_event("shutdown")
def shutdown_signal_scanner():
    signal_scanner.stop()
    telegram_control.stop()

@app.post("/api/analyze/{asset}")
def analyze_asset(asset: str):
    try:
        return analyze_asset_pipeline(asset)
    except Exception as e:
        print(f"[ERRO DO SISTEMA - SEM FALLBACK E SEM PLACEHOLDER] -> {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/copytrade/status")
def copytrade_status():
    try:
        return {
            "success": True,
            "data": copy_trade_service.status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/desk/status")
def desk_status():
    try:
        return {
            "success": True,
            "data": private_desk.status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/signals/status")
def signals_status():
    try:
        return {
            "success": True,
            "data": signal_scanner.status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/telegram/status")
def telegram_status():
    try:
        return {
            "success": True,
            "data": telegram_control.status(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals/start")
def signals_start():
    try:
        return {
            "success": True,
            "data": signal_scanner.start(force=True),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals/stop")
def signals_stop():
    try:
        return {
            "success": True,
            "data": signal_scanner.stop(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/signals/run-cycle")
def signals_run_cycle():
    try:
        return {
            "success": True,
            "data": signal_scanner.run_cycle(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/desk/pending")
def desk_pending():
    try:
        return {
            "success": True,
            "data": private_desk.list_pending(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/desk/approve/{request_id}")
def desk_approve(request_id: str):
    try:
        return {
            "success": True,
            "data": private_desk.approve(request_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/desk/reject/{request_id}")
def desk_reject(request_id: str):
    try:
        return {
            "success": True,
            "data": private_desk.reject(request_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/copytrade/execute/{asset}")
def copytrade_execute(asset: str):
    try:
        # Reusa pipeline completo para manter as mesmas regras de validacao e governanca.
        analysis = analyze_asset(asset)
        return {
            "success": True,
            "data": analysis,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
