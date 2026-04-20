from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .telegram_bot import UniIATelegramBot
from .copy_trade import CopyTradeService
from .desk import PrivateDesk
from ..agents.news_agent import NewsAgent
from ..agents.sentiment_agent import SentimentAgent
from ..agents.macro_agent import MacroAgent
from ..agents.trends_agent import TrendsAgent
from ..agents.technical_agent import TechnicalAgent
from ..agents.fundamentalist_agent import FundamentalistAgent
from ..agents.position_monitor_agent import PositionMonitorAgent
from ..agents.orchestrator_agent import OrchestratorAgent

app = FastAPI(
    title="UNI IA",
    description="API Mestre de Orquestração com Sinais de Alta Performance via IA Multi-Framework",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

telegram_bot = UniIATelegramBot()
copy_trade_service = CopyTradeService()
private_desk = PrivateDesk(copy_trade_service)

@app.post("/api/analyze/{asset}")
def analyze_asset(asset: str):
    try:
        print(f"[{asset}] INICIANDO VARREDURA PROFUNDA UNI IA...")
        
        agents_data = []

        # 1. MacroAgent
        macro = MacroAgent().analyze_macro_context(asset)
        agents_data.append(macro)
        print(f"[{asset}] Macro OK: {macro.signal_type}")
        
        # 2. TrendsAgent
        trends = TrendsAgent().analyze_trends(asset)
        agents_data.append(trends)
        print(f"[{asset}] Trends OK: {trends.signal_type}")

        # 3. TechnicalAgent (Múltiplos Tempos Gráficos)
        tech = TechnicalAgent().analyze_technical(asset)
        agents_data.append(tech)
        print(f"[{asset}] Technical (Multi-TF) OK: {tech.signal_type}")

        # 4. FundamentalistAgent (Dados Financeiros Históricos da Base de Valores)
        fund = FundamentalistAgent().analyze_fundamentals(asset)
        agents_data.append(fund)
        print(f"[{asset}] Funamentalist OK: {fund.signal_type}")

        # 5. NewsAgent & SentimentAgent 
        news = NewsAgent().analyze_news(asset)
        agents_data.append(news)
        print(f"[{asset}] News OK: {news.signal_type}")

        senti = SentimentAgent().analyze_sentiment(asset, news.raw_data)
        agents_data.append(senti)
        print(f"[{asset}] Sentiment/Psico OK: {senti.signal_type}")

        # 6. Orchestrator Mestre Ph.D
        orchestrator = OrchestratorAgent()
        alert = orchestrator.analyze_signals(asset, agents_data)
        
        # 7. Monitor Guardião: Usuários em Operação Aberta
        guard = PositionMonitorAgent().verify_reversal_risk(alert)
        if guard.get("is_reversal_alert"):
            alert.position_reversal_alert = guard.get("reversal_message")
            print(f"[{asset}] 🔥 ALERTA DE REVERSÃO DE POSIÇÃO ATIVADO!")

        # Disparo Telegram Bot da UNI IA
        telegram_bot.dispatch_alert(alert)

        desk_result = private_desk.handle_alert(alert)
        
        return {
            "success": True,
            "data": alert.dict(),
            "desk": desk_result,
        }

    except Exception as e:
        import traceback
        print(f"[ERRO DO SISTEMA - SEM FALLBACK E SEM PLACEHOLDER] -> {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Erro interno na análise. Verifique os logs do servidor.")


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
        import traceback
        print(f"[ERRO COPYTRADE] -> {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Erro interno na execução. Verifique os logs do servidor.")
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
