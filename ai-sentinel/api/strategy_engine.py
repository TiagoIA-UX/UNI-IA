import os
from typing import List

from core.schemas import AgentSignal, OpportunityAlert, StrategyDecision


class StrategyEngine:
    def __init__(self):
        self.weights = {
            "TechnicalAgent": 0.30,
            "TrendsAgent": 0.25,
            "SentimentAgent": 0.15,
            "NewsAgent": 0.10,
            "MacroAgent": 0.10,
            "FundamentalistAgent": 0.10,
        }
        self.default_mode = os.getenv("STRATEGY_DEFAULT_MODE", "swing").lower()

    def build_decision(self, asset: str, signals: List[AgentSignal], alert: OpportunityAlert) -> StrategyDecision:
        weighted_bias = 0.0
        reasons: List[str] = []

        for signal in signals:
            polarity = self._polarity(signal.signal_type)
            weight = self.weights.get(signal.agent_name, 0.0)
            weighted_bias += polarity * weight * (float(signal.confidence) / 100.0)
            if signal.summary:
                reasons.append(f"{signal.agent_name}: {signal.summary}")

        direction = self._direction(weighted_bias, alert)
        timeframe = self._timeframe(self.default_mode)
        confidence = min(99.0, max(0.0, float(alert.score)))
        operational_status = self._operational_status(alert)
        execution_hint = self._execution_hint(direction, timeframe, alert.classification)

        return StrategyDecision(
            mode=self.default_mode,
            direction=direction,
            timeframe=timeframe,
            confidence=confidence,
            operational_status=operational_status,
            reasons=reasons[:4],
            execution_hint=execution_hint,
        )

    def _polarity(self, signal_type: str) -> float:
        normalized = (signal_type or "").upper()
        positive_tokens = ["BUY", "BULL", "POSITIVE", "RISK-ON", "FOMO", "UNDERVALUED"]
        negative_tokens = ["SELL", "BEAR", "NEGATIVE", "RISK-OFF", "FEAR", "OVERVALUED"]
        if any(token in normalized for token in positive_tokens):
            return 1.0
        if any(token in normalized for token in negative_tokens):
            return -1.0
        return 0.0

    def _direction(self, weighted_bias: float, alert: OpportunityAlert) -> str:
        explanation = (alert.explanation or "").upper()
        if "VENDA" in explanation or "SELL" in explanation:
            return "short"
        if "COMPRA" in explanation or "BUY" in explanation:
            return "long"
        if alert.classification == "RISCO" and weighted_bias <= 0:
            return "short"
        if alert.classification == "OPORTUNIDADE" and weighted_bias >= 0:
            return "long"
        return "flat"

    def _timeframe(self, mode: str) -> str:
        mapping = {
            "day_trade": "15m-1h",
            "swing": "4h-1d",
            "position": "1d-1w",
            "portfolio": "1w-1mo",
        }
        return mapping.get(mode, "4h-1d")

    def _operational_status(self, alert: OpportunityAlert) -> str:
        if alert.classification == "OPORTUNIDADE":
            return "monitorando_execucao"
        if alert.classification == "RISCO":
            return "modo_defensivo"
        return "somente_observacao"

    def _execution_hint(self, direction: str, timeframe: str, classification: str) -> str:
        if direction == "flat":
            return "Aguardar nova confluencia antes de executar."
        if classification != "OPORTUNIDADE":
            return f"Execucao restrita; operar apenas com protecao reforcada no timeframe {timeframe}."
        return f"Priorizar entrada alinhada a {direction} no timeframe {timeframe}."