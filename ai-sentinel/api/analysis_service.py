from core.schemas import OpportunityAlert


class AnalysisService:
    def analyze(self, asset: str) -> OpportunityAlert:
        from agents.news_agent import NewsAgent
        from agents.sentiment_agent import SentimentAgent
        from agents.macro_agent import MacroAgent
        from agents.trends_agent import TrendsAgent
        from agents.technical_agent import TechnicalAgent
        from agents.fundamentalist_agent import FundamentalistAgent
        from agents.position_monitor_agent import PositionMonitorAgent
        from agents.orchestrator_agent import OrchestratorAgent
        from api.strategy_engine import StrategyEngine

        print(f"[{asset}] INICIANDO VARREDURA PROFUNDA UNI IA...")

        agents_data = []

        macro = MacroAgent().analyze_macro_context(asset)
        agents_data.append(macro)
        print(f"[{asset}] Macro OK: {macro.signal_type}")

        trends = TrendsAgent().analyze_trends(asset)
        agents_data.append(trends)
        print(f"[{asset}] Trends OK: {trends.signal_type}")

        tech = TechnicalAgent().analyze_technical(asset)
        agents_data.append(tech)
        print(f"[{asset}] Technical (Multi-TF) OK: {tech.signal_type}")

        fund = FundamentalistAgent().analyze_fundamentals(asset)
        agents_data.append(fund)
        print(f"[{asset}] Funamentalist OK: {fund.signal_type}")

        news = NewsAgent().analyze_news(asset)
        agents_data.append(news)
        print(f"[{asset}] News OK: {news.signal_type}")

        senti = SentimentAgent().analyze_sentiment(asset, news.raw_data)
        agents_data.append(senti)
        print(f"[{asset}] Sentiment/Psico OK: {senti.signal_type}")

        orchestrator = OrchestratorAgent()
        alert = orchestrator.analyze_signals(asset, agents_data)
        strategy_engine = StrategyEngine()
        alert.strategy = strategy_engine.build_decision(asset, agents_data, alert)

        guard = PositionMonitorAgent().verify_reversal_risk(alert)
        if guard.get("is_reversal_alert"):
            alert.position_reversal_alert = guard.get("reversal_message")
            print(f"[{asset}] ALERTA DE REVERSAO DE POSICAO ATIVADO")

        return alert