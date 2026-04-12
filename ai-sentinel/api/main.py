from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .telegram_bot import ZairyxTelegramBot
from ..agents.news_agent import NewsAgent
from ..agents.sentiment_agent import SentimentAgent
from ..agents.macro_agent import MacroAgent
from ..agents.trends_agent import TrendsAgent
from ..agents.technical_agent import TechnicalAgent
from ..agents.fundamentalist_agent import FundamentalistAgent
from ..agents.position_monitor_agent import PositionMonitorAgent
from ..agents.orchestrator_agent import OrchestratorAgent

app = FastAPI(
    title="Uni IA - by Zairyx IA",
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

@app.post("/api/analyze/{asset}")
def analyze_asset(asset: str):
    try:
        print(f"[{asset}] INICIANDO VARREDURA PROFUNDA MILITAR ZAIRYX IA...")
        
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

        # Disparo Zairyx Telegram Bot
        bot = ZairyxTelegramBot()
        bot.dispatch_alert(alert)
        
        return {
            "success": True,
            "data": alert.dict()
        }

    except Exception as e:
        print(f"[ERRO DO SISTEMA - SEM FALLBACK E SEM PLACEHOLDER] -> {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
