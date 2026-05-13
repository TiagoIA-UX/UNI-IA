from pathlib import Path
import os as _os
import logging
import threading
from typing import Dict, Any, List, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
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
from api.security import require_admin_token
from adapters.mercadobitcoin_market import get_candles as mb_get_candles, get_ticker as mb_get_ticker, normalize_mb_market
from core.chart_timeframes import normalize_chart_timeframe, public_timeframes_catalog
from core.daily_ops_report import DailyOpsReportService
from core.kill_switch import KillSwitchService
from core.system_state import SystemStateManager, UniIAMode

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
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-UNI-IA-ADMIN-TOKEN"],
)

# --- Inicialização de Singletons ---
try:
    _mode_raw = (_os.getenv("UNI_IA_MODE", "paper") or "paper").strip().lower()
    try:
        system_state = SystemStateManager(UniIAMode(_mode_raw))
    except ValueError:
        system_state = SystemStateManager(UniIAMode.PAPER)

    telegram_bot = UniIATelegramBot()
    audit_service = AuditService()
    copy_trade_service = CopyTradeService()
    private_desk = PrivateDesk(copy_trade_service, audit_service)
    analysis_service = AnalysisService(system_state=system_state)
    signal_scanner = SignalScanner(analysis_service, telegram_bot, private_desk, audit_service)
    telegram_control = TelegramControlService(telegram_bot, private_desk, signal_scanner, copy_trade_service)
    kill_switch_service = KillSwitchService()
    daily_ops_service = DailyOpsReportService()
    logger.info("Todos os serviços integrados com sucesso.")
except Exception as init_err:
    logger.error(f"Falha crítica na inicialização dos serviços: {init_err}")
    raise init_err


class AnalyzeRequestBody(BaseModel):
    """Corpo opcional do POST /api/analyze — alinha motor ao timeframe do grafico na UI."""
    timeframe: Optional[str] = Field(
        None,
        description="Intervalo canonico (ex: 1m, 5m, 1h, 1wk). Lista em GET /api/meta/chart-timeframes",
    )
    tf_label: Optional[str] = Field(None, description="Label opcional da UI (ex: M1, H4)")


# --- Modelos de Dados (Schemas) ---
class OperationRequest(BaseModel):
    symbol: str = Field(..., description="Símbolo do par de negociação (ex: BTCBRL)")
    amount: float = Field(..., gt=0, description="Quantidade da operação")
    price: float = Field(..., gt=0, description="Preço de execução")
    side: str = Field(..., description="Lado da operação: BUY ou SELL")

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        if v.upper() not in ("BUY", "SELL"):
            raise ValueError("O lado deve ser BUY ou SELL")
        return v.upper()


class DeskExecuteBody(BaseModel):
    """Corpo de POST /api/desk/execute — ordem manual pela plataforma ou integração."""
    asset: str = Field(..., description="Par ou base, ex: BTCBRL, BTC-BRL, BTCUSDT")
    side: str = Field(..., description="BUY ou SELL (COMPRA/VENDA aceitos)")
    risk_percent: float = Field(1.0, gt=0, le=100, description="Metadado de risco (auditoria)")
    source: str = Field("plataforma-web", description="Origem do disparo")
    quantity: Optional[str] = Field(None, description="Quantidade da ordem; default MB_DEFAULT_QTY / BYBIT_DEFAULT_QTY")
    chart_timeframe: Optional[str] = Field(None, description="Timeframe canónico da UI (GET /api/meta/chart-timeframes)")
    auto_mode_context: Optional[bool] = Field(None, description="Se o utilizador tinha modo automático ligado na UI")

    @field_validator("asset")
    @classmethod
    def strip_asset(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("asset obrigatorio")
        return s

    @field_validator("side")
    @classmethod
    def normalize_side(cls, v: str) -> str:
        u = (v or "").strip().upper()
        if u not in ("BUY", "SELL", "COMPRA", "VENDA"):
            raise ValueError("side deve ser BUY, SELL, COMPRA ou VENDA")
        return u


# Mapeamento entre IDs do frontend e nomes canonicos de agentes no FeatureStore.
_FRONTEND_AGENT_FEATURE_MAP = {
    "ATLAS": "ATLAS",
    "MACRO": "MacroAgent",
    "ORION": "ORION",
    "NEWS": "NewsAgent",
    "TRENDS": "TrendsAgent",
    "FUND": "FundamentalistAgent",
    "SENTIMENT": "SentimentAgent",
}


def _collect_agent_scores(signal_id: str, alert) -> Dict[str, Any]:
    """Constroi mapa de scores por agente baseado em dados reais persistidos (sem placeholders)."""
    fm = analysis_service.feature_store.get_signal_feature_map(signal_id)
    scores: Dict[str, Any] = {}
    for frontend_id, agent_name in _FRONTEND_AGENT_FEATURE_MAP.items():
        entry = fm.get(agent_name) or {}
        feats = entry.get("features") or {}
        emitted = feats.get("emitted_confidence")
        if isinstance(emitted, (int, float)):
            scores[frontend_id] = round(float(emitted), 2)
        else:
            scores[frontend_id] = None

    if alert.governance:
        scores["SENTINEL"] = round(float(alert.governance.sentinel_confidence), 2)
    else:
        scores["SENTINEL"] = None

    scores["AEGIS"] = round(float(alert.score), 2) if isinstance(alert.score, (int, float)) else None

    argus_active = analysis_service.argus.get_active_positions() or []
    scores["ARGUS"] = 100.0 if argus_active else None

    return scores


def _analyze_async_side_effects_enabled() -> bool:
    """Quando True, Telegram + mesa + ARGUS correm em background — resposta HTTP volta mais cedo."""
    return str(_os.getenv("ANALYZE_ASYNC_SIDE_EFFECTS", "true")).strip().lower() in ("1", "true", "yes", "on")


def _run_analyze_side_effects(alert, desk_preview: Dict[str, Any]) -> None:
    """Telegram, mesa e registo ARGUS (apos /api/analyze devolver JSON)."""
    try:
        try:
            dispatched = bool(
                telegram_bot.dispatch_alert(alert, operational_context=desk_preview)
            )
            if not dispatched:
                logger.info("Telegram: nenhuma mensagem publica (filtros/gates ou skip).")
        except Exception as telegram_error:
            logger.error("Falha no despacho Telegram: %s", telegram_error)

        try:
            desk_result = private_desk.handle_alert(alert)
        except Exception as desk_error:
            logger.warning("Mesa bloqueou alerta sem derrubar /api/analyze: %s", desk_error)
            desk_result = {
                "success": False,
                "mode": desk_preview.get("mode"),
                "action": "blocked",
                "operational_status": str(desk_error),
            }
        try:
            analysis_service.register_argus_after_desk_pipeline(alert, desk_result)
        except Exception as reg_err:
            logger.warning("register_argus_after_desk_pipeline: %s", reg_err)
    except Exception as err:
        logger.exception("Efeitos colaterais pos-analise falharam: %s", err)


# --- Pipeline de Análise Original ---
def analyze_asset_pipeline(asset: str, chart_timeframe: Optional[str] = None) -> Dict[str, Any]:
    alert = analysis_service.analyze(asset, chart_timeframe=chart_timeframe)
    desk_preview = private_desk.preview_action(alert)

    try:
        audit_service.log_event(
            "signal.analysis_api",
            "success",
            asset=alert.asset,
            classification=alert.classification,
            score=float(alert.score),
            details={
                "strategy": alert.strategy.dict() if alert.strategy else None,
                "sources": alert.sources,
                "chart_timeframe": getattr(alert, "chart_timeframe", None),
            },
        )
    except Exception as audit_error:
        logger.warning(f"Erro ao registrar auditoria: {audit_error}")

    signal_id = alert.governance.signal_id if alert.governance else ""
    agent_scores = _collect_agent_scores(signal_id, alert) if signal_id else {}
    agent_failures = [f.dict() for f in (alert.agent_failures or [])]

    tf_snap = chart_timeframe or alert.chart_timeframe
    try:
        analysis_service.record_plataforma_signal(
            alert.asset,
            tf_snap,
            {
                "alert_data": alert.dict(),
                "agent_scores": agent_scores,
                "agent_failures": agent_failures,
                "fast_path_decision": alert.fast_path_decision,
            },
        )
    except Exception as cache_err:
        logger.warning("record_plataforma_signal: %s", cache_err)

    if _analyze_async_side_effects_enabled():
        threading.Thread(
            target=_run_analyze_side_effects,
            args=(alert, desk_preview),
            daemon=True,
            name="analyze-side-effects",
        ).start()
        telegram_result: Dict[str, Any] = {"success": True, "async": True, "dispatched": None}
        desk_result: Dict[str, Any] = {"success": True, "async": True, "action": "pending"}
    else:
        telegram_result = {"success": True, "dispatched": False}
        try:
            telegram_result["dispatched"] = bool(
                telegram_bot.dispatch_alert(alert, operational_context=desk_preview)
            )
        except Exception as telegram_error:
            logger.error(f"Falha no despacho Telegram: {telegram_error}")
            telegram_result = {"success": False, "dispatched": False, "error": str(telegram_error)}

        try:
            desk_result = private_desk.handle_alert(alert)
        except Exception as desk_error:
            logger.warning("Mesa bloqueou alerta sem derrubar /api/analyze: %s", desk_error)
            desk_result = {
                "success": False,
                "mode": desk_preview.get("mode"),
                "action": "blocked",
                "operational_status": str(desk_error),
            }
        try:
            analysis_service.register_argus_after_desk_pipeline(alert, desk_result)
        except Exception as reg_err:
            logger.warning("register_argus_after_desk_pipeline: %s", reg_err)

    return {
        "success": True,
        "data": alert.dict(),
        "agent_scores": agent_scores,
        "agent_failures": agent_failures,
        "integrity_score": float(alert.integrity_score),
        "fast_path_decision": alert.fast_path_decision,
        "telegram": telegram_result,
        "desk": desk_result,
    }


def _normalize_asset_compact(asset: str) -> str:
    return (asset or "").strip().upper().replace("-", "")


def _infer_news_gate_suppressed(alert_data: Dict[str, Any], agent_failures: List[Dict[str, Any]]) -> bool:
    """Heuristica: noticia / gate ORION-NEWS quando o fluxo ficou bloqueado."""
    chunks: List[str] = []
    strat = alert_data.get("strategy") or {}
    if isinstance(strat, dict):
        for r in strat.get("reasons") or []:
            chunks.append(str(r))
    chunks.append(str(alert_data.get("explanation") or ""))
    expl_blob = " ".join(chunks).lower()
    news_hints = (
        "noticia",
        "notícia",
        "news",
        "arara",
        "newsagent",
        "hot headline",
        "janela de risco",
        "cpi",
        "copom",
        "fomc",
        "selic",
    )
    if any(h in expl_blob for h in news_hints):
        return True
    for f in agent_failures:
        an = str(f.get("agent_name") or "")
        msg = str(f.get("error_message") or "").lower()
        if an in {"NewsAgent", "ORION"} and any(k in msg for k in ("news", "noticia", "gate", "hot", "block", "shock")):
            return True
    return False


def _build_signal_summary_payload(asset: str, timeframe: Optional[str]) -> Dict[str, Any]:
    """Constroi resposta plana para a mesa (UI). Usa cache do ultimo POST /api/analyze no mesmo TF."""
    norm_asset = _normalize_asset_compact(asset)
    tf = normalize_chart_timeframe(timeframe) if timeframe else None
    if not tf:
        tf = normalize_chart_timeframe("1h")
    if not tf:
        tf = "1h"

    cached = analysis_service.get_plataforma_signal(norm_asset, tf)
    ranking = analysis_service.outcome_tracker.asset_hit_ranking(
        timeframe=tf,
        window_days=90,
        min_trades=1,
    )
    hit_rate_pct: Optional[float] = None
    hit_rate_trades: Optional[int] = None
    for it in ranking.get("items") or []:
        if _normalize_asset_compact(str(it.get("asset") or "")) == norm_asset:
            trades = int(it.get("trades") or 0)
            if trades >= 5:
                hit_rate_pct = round(float(it.get("hit_rate_pct") or 0.0), 2)
                hit_rate_trades = trades
            break

    if not cached:
        return {
            "asset": norm_asset,
            "decision": None,
            "confidence": None,
            "signal_color": "gray",
            "hit_rate_pct": hit_rate_pct,
            "hit_rate_trades": hit_rate_trades,
            "hit_rate_window_days": 90,
            "last_updated": None,
            "blocking_reason": "Aguarde a analise (POST /api/analyze) para este ativo e timeframe.",
            "agent_scores": {},
            "fast_scalp_mode": False,
            "news_gate_suppressed": False,
            "chart_timeframe": tf,
            "cache_hit": False,
        }

    alert = cached.get("alert_data") or {}
    agent_scores = cached.get("agent_scores") or {}
    failures = list(cached.get("agent_failures") or [])
    fp = str(cached.get("fast_path_decision") or alert.get("fast_path_decision") or "block").lower()
    strategy = alert.get("strategy") or {}
    dir_raw = str(strategy.get("direction") or "flat").lower()
    try:
        aegis_score = float(alert.get("score") if alert.get("score") is not None else 0.0)
    except (TypeError, ValueError):
        aegis_score = 0.0

    blocking_reason: Optional[str] = None
    if fp == "block":
        decision = "BLOQUEADO"
        reasons = [str(x) for x in (strategy.get("reasons") or []) if x is not None]
        blocking_reason = "; ".join(reasons[:4]) if reasons else "Fast path bloqueou o gatilho (decision=block)."
    elif aegis_score >= 75.0 and dir_raw == "long":
        decision = "COMPRA"
    elif aegis_score >= 75.0 and dir_raw == "short":
        decision = "VENDA"
    else:
        decision = "NEUTRO"

    color_map = {"COMPRA": "green", "VENDA": "red", "NEUTRO": "amber", "BLOQUEADO": "gray"}
    news_sup = _infer_news_gate_suppressed(alert, failures) and decision == "BLOQUEADO"
    fast_scalp = str(strategy.get("mode") or "") == "fast_scalp"

    return {
        "asset": norm_asset,
        "decision": decision,
        "confidence": round(aegis_score, 2),
        "signal_color": color_map.get(decision, "gray"),
        "hit_rate_pct": hit_rate_pct,
        "hit_rate_trades": hit_rate_trades,
        "hit_rate_window_days": 90,
        "last_updated": cached.get("recorded_at"),
        "blocking_reason": blocking_reason,
        "agent_scores": agent_scores,
        "fast_scalp_mode": fast_scalp,
        "news_gate_suppressed": news_sup,
        "chart_timeframe": tf,
        "cache_hit": True,
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

# --- Readiness / Operational reports -----------------------------------------

_READINESS_SEVERITY_ORDER = {"info": 0, "warning": 1, "critical": 2}


def _audit_table_validated() -> bool:
    table = (_os.getenv("AUDIT_TABLE_NAME", "") or "").strip()
    if not table:
        return False
    if table not in AuditService.SUPPORTED_AUDIT_TABLES:
        return False
    if table == "uni_ia_events":
        variant = (_os.getenv("AUDIT_EVENT_VARIANT", "A") or "A").strip().upper()
        if variant not in {"A", "B"}:
            return False
    return True


def _collect_readiness_matrix() -> Dict[str, Any]:
    """Constroi a matriz de readiness operacional usada por /api/health/ready e /api/reports/ops-summary."""
    audit_table = (_os.getenv("AUDIT_TABLE_NAME", "") or "").strip()
    audit_validated = _audit_table_validated()
    audit_supabase_ready = audit_service.is_ready()
    audit_ready = audit_validated and audit_supabase_ready

    telegram_control_state = telegram_control.status()
    telegram_control_enabled = bool(telegram_control_state.get("enabled"))
    telegram_control_configured = bool(telegram_control_state.get("configured"))
    telegram_ready = (not telegram_control_enabled) or telegram_control_configured

    telegram_dispatch_ready = telegram_bot.configured()

    desk_state = private_desk.status()
    desk_store_ready = bool(desk_state.get("persistence_ready"))

    copy_trade_state = copy_trade_service.status()
    scanner_state = signal_scanner.status()

    checks: Dict[str, bool] = {
        "audit_ready": audit_ready,
        "telegram_ready": telegram_ready,
        "telegram_dispatch_ready": telegram_dispatch_ready,
        "desk_store_ready": desk_store_ready,
    }

    reason_details: List[Dict[str, str]] = []
    if not audit_ready:
        reason_details.append({"check": "audit_ready", "reason": "audit_not_ready", "severity": "critical"})
    if not telegram_ready:
        reason_details.append({"check": "telegram_ready", "reason": "telegram_control_not_ready", "severity": "warning"})
    if not telegram_dispatch_ready:
        reason_details.append({"check": "telegram_dispatch_ready", "reason": "telegram_dispatch_not_ready", "severity": "warning"})
    if not desk_store_ready:
        reason_details.append({"check": "desk_store_ready", "reason": "desk_store_not_ready", "severity": "critical"})

    failed_checks = [item["check"] for item in reason_details]
    reasons = [item["reason"] for item in reason_details]

    overall_severity = "info"
    for item in reason_details:
        if _READINESS_SEVERITY_ORDER[item["severity"]] > _READINESS_SEVERITY_ORDER[overall_severity]:
            overall_severity = item["severity"]

    return {
        "ready": not failed_checks,
        "checks": checks,
        "failed_checks": failed_checks,
        "reasons": reasons,
        "reason_details": reason_details,
        "overall_severity": overall_severity,
        "system": system_state.snapshot(),
        "scanner": scanner_state,
        "telegram": {
            "control": telegram_control_state,
            "dispatch_configured": telegram_dispatch_ready,
            "ready": telegram_ready,
        },
        "copy_trade": copy_trade_state,
        "desk": desk_state,
        "risk": kill_switch_service.get_status(
            outcome_tracker=analysis_service.outcome_tracker,
            system_state=system_state,
        ),
        "audit": {
            "table": audit_table,
            "validated": audit_validated,
            "supabase_ready": audit_supabase_ready,
        },
    }


@app.get("/api/health/ready", tags=["Monitoramento"])
def health_readiness(_: None = Depends(require_admin_token)):
    """Matriz de readiness para producao (audit, telegram, desk_store, etc.)."""
    try:
        return {"success": True, "data": _collect_readiness_matrix()}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("health_readiness")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/ops-summary", tags=["Monitoramento"])
def reports_ops_summary(
    date: Optional[str] = None,
    risk_events_limit: int = 5,
    dispatch_window_minutes: int = 1440,
    dispatch_sample_limit: int = 5000,
    _: None = Depends(require_admin_token),
):
    """Resumo operacional consolidado: daily report + risk + dispatch + readiness."""
    from datetime import date as _date_cls
    from datetime import datetime as _dt_cls

    report_date: Optional[_date_cls] = None
    if date:
        try:
            report_date = _dt_cls.strptime(str(date), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="date_invalido (use YYYY-MM-DD)")

    try:
        daily_report = daily_ops_service.generate_daily_report(report_date=report_date)
    except RuntimeError as e:
        daily_report = {
            "success": False,
            "error": str(e),
            "totals": {},
            "by_asset": {},
        }

    try:
        risk_status = kill_switch_service.get_status(
            outcome_tracker=analysis_service.outcome_tracker,
            system_state=system_state,
        )
    except Exception as e:
        risk_status = {"enabled": kill_switch_service.enabled, "error": str(e)}

    risk_recent = kill_switch_service.get_recent_events(limit=int(risk_events_limit or 0))

    dispatch_metrics = {
        "window_minutes": int(dispatch_window_minutes),
        "sample_limit": int(dispatch_sample_limit),
        "totals": daily_report.get("totals", {}),
        "top_reasons_block": daily_report.get("top_reasons_block", []),
        "by_asset": daily_report.get("by_asset", {}),
        "source": daily_report.get("source", {}),
    }

    readiness = _collect_readiness_matrix()
    strict_readiness = readiness["overall_severity"] == "info"

    return {
        "success": True,
        "data": {
            "daily_report": daily_report,
            "risk_status": risk_status,
            "risk_recent_events": risk_recent,
            "dispatch_metrics": dispatch_metrics,
            "system": readiness["system"],
            "desk": readiness["desk"],
            "copy_trade": readiness["copy_trade"],
            "scanner": readiness["scanner"],
            "strict_readiness": strict_readiness,
            "checks": readiness["checks"],
            "failed_checks": readiness["failed_checks"],
            "reasons": readiness["reasons"],
            "reason_details": readiness["reason_details"],
            "overall_severity": readiness["overall_severity"],
            "readiness": {
                "ready": readiness["ready"],
                "checks": readiness["checks"],
                "failed_checks": readiness["failed_checks"],
                "reasons": readiness["reasons"],
                "reason_details": readiness["reason_details"],
                "overall_severity": readiness["overall_severity"],
            },
        },
    }


@app.get("/api/signals/status", tags=["Monitoramento"])
def signals_status():
    """Status consolidado do scanner (sem scores sinteticos: so estado real)."""
    try:
        real_status = signal_scanner.status()
        if not real_status:
            raise HTTPException(status_code=503, detail="scanner_status_indisponivel")
        return {"success": True, "data": real_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoints de Gestão de Sinais ---

@app.post("/api/analyze/{asset}", tags=["Sinais"])
def analyze_asset(asset: str, body: Optional[AnalyzeRequestBody] = Body(default=None)):
    chart_tf = normalize_chart_timeframe(body.timeframe) if body else None
    try:
        return analyze_asset_pipeline(asset, chart_timeframe=chart_tf)
    except Exception as e:
        logger.error(f"Erro na análise do ativo {asset}: {e}")
        msg = str(e)
        agent_scores = {frontend_id: None for frontend_id in _FRONTEND_AGENT_FEATURE_MAP}
        agent_scores.update({"SENTINEL": None, "AEGIS": None, "ARGUS": None})
        return {
            "success": False,
            "data": {
                "asset": asset,
                "score": 0.0,
                "classification": "RISCO",
                "explanation": f"Analise degradada: {msg}",
                "sources": [],
                "strategy": {
                    "mode": "degradado",
                    "direction": "flat",
                    "timeframe": chart_tf or "n/a",
                    "confidence": 0.0,
                    "operational_status": "analysis_degraded",
                    "reasons": [msg],
                },
                "governance": None,
                "chart_timeframe": chart_tf,
                "agent_failures": [
                    {
                        "agent_name": "PIPELINE",
                        "error_type": type(e).__name__,
                        "error_message": msg[:512],
                        "is_critical": True,
                    }
                ],
                "integrity_score": 0.0,
                "fast_path_decision": "block",
            },
            "agent_scores": agent_scores,
            "agent_failures": [
                {
                    "agent_name": "PIPELINE",
                    "error_type": type(e).__name__,
                    "error_message": msg[:512],
                    "is_critical": True,
                }
            ],
            "integrity_score": 0.0,
            "fast_path_decision": "block",
            "telegram": {"success": False, "dispatched": False, "error": msg[:512]},
            "desk": {"success": False, "action": "blocked", "operational_status": msg[:512]},
        }


@app.get("/api/meta/chart-timeframes", tags=["Metadados"])
def meta_chart_timeframes():
    """Timeframes suportados pelo motor, alinhados ao embed TradingView."""
    return {"success": True, "items": public_timeframes_catalog()}


@app.get("/api/market/mb/ticker", tags=["Mercado"])
def market_mb_ticker(asset: str):
    try:
        market = normalize_mb_market(asset)
        return {"success": True, "data": mb_get_ticker(market)}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/market/mb/candles", tags=["Mercado"])
def market_mb_candles(asset: str, granularity: int = 900, limit: int = 120):
    try:
        market = normalize_mb_market(asset)
        return {"success": True, "data": {"market": market, "candles": mb_get_candles(market, granularity, limit)}}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/performance/asset-hit-ranking", tags=["Performance"])
def performance_asset_hit_ranking(
    timeframe: str,
    window_days: int = 90,
    min_trades: int = 1,
):
    """Ranking por taxa de acerto (wins / trades decisivos) por ativo no timeframe."""
    tf = normalize_chart_timeframe(timeframe)
    if not tf:
        raise HTTPException(status_code=400, detail="timeframe_invalido")
    data = analysis_service.outcome_tracker.asset_hit_ranking(
        timeframe=tf,
        window_days=window_days,
        min_trades=min_trades,
    )
    return {"success": True, "data": data}


@app.get("/api/signal/summary/{asset}", tags=["Sinais"])
def signal_summary(asset: str, timeframe: Optional[str] = None):
    """Estado consolidado do sinal para a mesa (cache do ultimo POST /api/analyze no mesmo TF)."""
    return _build_signal_summary_payload(asset, timeframe)


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


@app.post("/api/desk/execute", tags=["Broker"])
def desk_execute(body: DeskExecuteBody):
    """Executa ordem manual (paper ou live no broker conforme UNI_IA_MODE)."""
    try:
        chart_tf = (
            normalize_chart_timeframe(body.chart_timeframe)
            if body.chart_timeframe
            else None
        )
        data = private_desk.execute_manual_order(
            asset=body.asset,
            side=body.side,
            risk_percent=body.risk_percent,
            source=body.source,
            quantity=body.quantity,
            chart_timeframe=chart_tf,
            auto_mode_context=body.auto_mode_context,
        )
        if data.get("action") == "executed" and data.get("execution"):
            br = (data["execution"].get("broker_response") or {})
            price = br.get("price_brl")
            if isinstance(price, (int, float)) and float(price) > 0:
                try:
                    analysis_service.register_argus_after_manual_execution(
                        asset=str(data.get("symbol") or body.asset),
                        side=body.side,
                        entry_price=float(price),
                        chart_timeframe=chart_tf,
                        strategy_mode="manual_desk",
                    )
                except Exception as reg_err:
                    logger.warning("register_argus_after_manual_execution: %s", reg_err)
        return {"success": True, "data": data}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("desk_execute")
        raise HTTPException(status_code=500, detail=str(e))


def argus_register(body: Dict[str, Any], _=None):
    """Registo de posicao ARGUS (testes / integracoes internas)."""
    data = body or {}
    missing = [k for k in ("signal_id", "asset", "direction", "entry_price") if data.get(k) is None]
    if missing:
        raise ValueError(f"campos obrigatorios ausentes: {', '.join(missing)}")
    out = analysis_service.argus.register_position(
        signal_id=str(data["signal_id"]),
        request_id=data.get("request_id"),
        asset=str(data["asset"]),
        direction=str(data["direction"]).lower(),
        entry_price=float(data["entry_price"]),
        timeframe=data.get("timeframe"),
        strategy=data.get("strategy"),
    )
    return {"success": True, "data": out}


def argus_close(body: Dict[str, Any], _=None):
    data = body or {}
    if not data.get("signal_id"):
        raise ValueError("signal_id obrigatorio")
    out = analysis_service.argus.close_position(
        signal_id=str(data["signal_id"]),
        exit_price=float(data["exit_price"]),
        result=str(data["result"]),
    )
    return {"success": True, "data": out}


def outcomes_record(body: Dict[str, Any], _=None):
    """Grava outcome com correlacao a posicao ARGUS ativa (anti-orfaos)."""
    data = body or {}
    sid = data.get("signal_id")
    if not sid:
        raise ValueError("signal_id obrigatorio")
    pos = analysis_service.argus.get_active_position(str(sid))
    if not pos:
        raise RuntimeError(
            "Outcome rejeitado: falta correlacao verificavel com posicao ARGUS ativa."
        )
    for k in ("exit_price", "pnl_percent", "result"):
        if data.get(k) is None:
            raise ValueError(f"{k} obrigatorio")
    res = analysis_service.outcome_tracker.record_outcome(
        signal_id=str(sid),
        request_id=data.get("request_id") or pos.get("request_id"),
        asset=str(data.get("asset") or pos.get("asset", "")).upper(),
        direction=str(data.get("direction") or pos.get("direction", "long")).lower(),
        entry_price=float(data.get("entry_price", pos["entry_price"])),
        exit_price=float(data["exit_price"]),
        pnl_percent=float(data["pnl_percent"]),
        result=str(data["result"]),
        timeframe=data.get("timeframe") or pos.get("timeframe"),
        strategy=data.get("strategy") or pos.get("strategy"),
    )
    return {"success": True, "data": res}


@app.post("/api/admin/argus/register", tags=["Admin"])
def http_argus_register(
    body: Dict[str, Any] = Body(...),
    _auth: None = Depends(require_admin_token),
):
    """Regista posicao ARGUS (header `X-UNI-IA-ADMIN-TOKEN` = `UNI_IA_ADMIN_TOKEN`)."""
    try:
        return argus_register(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("http_argus_register")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/argus/close", tags=["Admin"])
def http_argus_close(
    body: Dict[str, Any] = Body(...),
    _auth: None = Depends(require_admin_token),
):
    """Fecha posicao ARGUS e grava outcome via fluxo do agente."""
    try:
        return argus_close(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("http_argus_close")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/outcomes/record", tags=["Admin"])
def http_outcomes_record(
    body: Dict[str, Any] = Body(...),
    _auth: None = Depends(require_admin_token),
):
    """Grava outcome correlacionado com posicao ARGUS ativa (anti-orfaos)."""
    try:
        return outcomes_record(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("http_outcomes_record")
        raise HTTPException(status_code=500, detail=str(e))


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