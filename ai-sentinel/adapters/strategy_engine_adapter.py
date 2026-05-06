import os
from typing import List, Optional

from api.strategy_engine import StrategyEngine
from core.execution_simulator import HistoricalCandle
from core.schemas import AgentSignal, OpportunityAlert
from core.signal_provider import MarketData, Signal


def _sma(values: List[float], period: int) -> Optional[float]:
    if len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / period


def _atr(candles: List[HistoricalCandle], period: int) -> Optional[float]:
    if len(candles) < period + 1:
        return None

    trs = []
    for idx in range(1, len(candles)):
        high = candles[idx].high
        low = candles[idx].low
        prev_close = candles[idx - 1].close
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))

    window = trs[-period:]
    return sum(window) / period if window else None


class StrategyEngineSignalProvider:
    def __init__(self):
        self.strategy_engine = StrategyEngine()
        self.fast_period = int(os.getenv("BACKTEST_FAST_SMA_PERIOD", "5"))
        self.slow_period = int(os.getenv("BACKTEST_SLOW_SMA_PERIOD", "20"))
        self.atr_period = int(os.getenv("BACKTEST_ATR_PERIOD", "14"))
        self.atr_multiplier = float(os.getenv("BACKTEST_ATR_MULTIPLIER", "1.5"))
        self.min_score = float(os.getenv("BACKTEST_MIN_SCORE", "70"))
        self.min_atr_pct = float(os.getenv("BACKTEST_MIN_ATR_PCT", "0.002"))
        self.take_profit_rr = float(os.getenv("BACKTEST_TAKE_PROFIT_RR", "2.0"))

    def generate(self, market_data: MarketData) -> Optional[Signal]:
        closes = [candle.close for candle in market_data.window]
        fast_sma = _sma(closes, self.fast_period)
        slow_sma = _sma(closes, self.slow_period)
        atr = _atr(market_data.window, self.atr_period)

        if fast_sma is None or slow_sma is None or atr is None:
            return None

        current_price = market_data.current_candle.close
        atr_pct = atr / current_price if current_price > 0 else 0.0
        if atr_pct < self.min_atr_pct:
            return None

        side = self._detect_side(current_price, fast_sma, slow_sma)
        if side is None:
            return None

        score = self._score(current_price, fast_sma, slow_sma, atr_pct)
        if score < self.min_score:
            return None

        alert = OpportunityAlert(
            asset=market_data.asset,
            score=score,
            classification="OPORTUNIDADE",
            explanation=self._build_explanation(side, fast_sma, slow_sma, current_price),
            sources=["backtest.strategy_engine_adapter"],
        )
        agent_signals = self._build_agent_signals(market_data.asset, side, score, fast_sma, slow_sma, atr_pct)
        decision = self.strategy_engine.build_decision(market_data.asset, agent_signals, alert)
        alert.strategy = decision

        if decision.direction == "flat":
            return None

        stop_distance = atr * self.atr_multiplier
        stop_loss = current_price - stop_distance if side == "long" else current_price + stop_distance
        take_profit = (
            current_price + stop_distance * self.take_profit_rr
            if side == "long"
            else current_price - stop_distance * self.take_profit_rr
        )

        return Signal(
            asset=market_data.asset,
            side=side,
            score=score,
            stop_loss=round(stop_loss, 8),
            take_profit=round(take_profit, 8),
            entry_reference_price=current_price,
            reasons=decision.reasons,
            metadata={
                "strategy_mode": decision.mode,
                "strategy_timeframe": decision.timeframe,
                "strategy_confidence": decision.confidence,
                "atr": round(atr, 8),
                "atr_pct": round(atr_pct, 8),
                "fast_sma": round(fast_sma, 8),
                "slow_sma": round(slow_sma, 8),
            },
        )

    def _detect_side(self, current_price: float, fast_sma: float, slow_sma: float) -> Optional[str]:
        if fast_sma > slow_sma and current_price > slow_sma:
            return "long"
        if fast_sma < slow_sma and current_price < slow_sma:
            return "short"
        return None

    def _score(self, current_price: float, fast_sma: float, slow_sma: float, atr_pct: float) -> float:
        spread_pct = abs(fast_sma - slow_sma) / current_price if current_price > 0 else 0.0
        raw_score = 60.0 + min(spread_pct * 2500.0, 25.0) + min(atr_pct * 500.0, 10.0)
        return round(min(raw_score, 99.0), 2)

    def _build_explanation(self, side: str, fast_sma: float, slow_sma: float, current_price: float) -> str:
        action = "BUY" if side == "long" else "SELL"
        return (
            f"{action} signal alinhado a tendencia. "
            f"Preco={current_price:.4f}, SMA rapida={fast_sma:.4f}, SMA lenta={slow_sma:.4f}."
        )

    def _build_agent_signals(
        self,
        asset: str,
        side: str,
        score: float,
        fast_sma: float,
        slow_sma: float,
        atr_pct: float,
    ) -> List[AgentSignal]:
        signal_type = "BUY" if side == "long" else "SELL"
        direction_label = "bullish" if side == "long" else "bearish"

        return [
            AgentSignal(
                agent_name="TechnicalAgent",
                asset=asset,
                signal_type=signal_type,
                confidence=score,
                summary=(
                    f"Tendencia {direction_label} com SMA rapida {'acima' if side == 'long' else 'abaixo'} "
                    f"da lenta ({fast_sma:.4f} vs {slow_sma:.4f})."
                ),
            ),
            AgentSignal(
                agent_name="TrendsAgent",
                asset=asset,
                signal_type=signal_type,
                confidence=max(score - 5.0, 0.0),
                summary=f"Momentum consistente com ATR percentual em {atr_pct:.4%}.",
            ),
        ]


def generate_signal(candles: List[HistoricalCandle], index: int) -> Optional[Signal]:
    asset = os.getenv("BACKTEST_ASSET", "BTCUSDT")
    provider = StrategyEngineSignalProvider()
    return provider.generate(MarketData(asset=asset, candles=candles, index=index))
