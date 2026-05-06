import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.portfolio_state import SimulatedTrade


@dataclass
class HistoricalCandle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestSignal:
    asset: str
    side: str
    score: float
    entry_reference_price: float
    stop_loss: float
    take_profit: Optional[float] = None
    position_size_multiplier: float = 1.0
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ExecutionSimulator:
    def __init__(
        self,
        *,
        fee_rate: Optional[float] = None,
        slippage_bps: Optional[float] = None,
        spread_bps: Optional[float] = None,
        risk_per_trade_pct: Optional[float] = None,
    ):
        self.fee_rate = fee_rate if fee_rate is not None else float(os.getenv("BACKTEST_FEE_RATE", "0.0006"))
        self.slippage_bps = slippage_bps if slippage_bps is not None else float(os.getenv("BACKTEST_SLIPPAGE_BPS", "3"))
        self.spread_bps = spread_bps if spread_bps is not None else float(os.getenv("BACKTEST_SPREAD_BPS", "1"))
        self.risk_per_trade_pct = (
            risk_per_trade_pct
            if risk_per_trade_pct is not None
            else float(os.getenv("BACKTEST_RISK_PER_TRADE_PCT", "1.0"))
        )

    def open_trade(self, signal: BacktestSignal, candle: HistoricalCandle, portfolio_cash: float) -> SimulatedTrade:
        side = signal.side.lower()
        if side not in {"long", "short"}:
            raise RuntimeError(f"Lado invalido para backtest: {signal.side}")

        entry_price = self._apply_entry_costs(candle.open, side)
        stop_loss = float(signal.stop_loss)
        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            raise RuntimeError("Stop loss invalido: distancia ate a entrada precisa ser positiva.")

        position_size_multiplier = max(float(signal.position_size_multiplier), 0.0)
        risk_amount = max(portfolio_cash * (self.risk_per_trade_pct / 100.0) * position_size_multiplier, 0.0)
        quantity = risk_amount / stop_distance
        fee_paid_entry = entry_price * quantity * self.fee_rate

        return SimulatedTrade(
            trade_id=str(uuid.uuid4()),
            asset=signal.asset,
            side=side,
            status="OPEN",
            entry_timestamp=candle.timestamp,
            entry_price=round(entry_price, 8),
            quantity=round(quantity, 8),
            stop_loss=round(stop_loss, 8),
            take_profit=round(signal.take_profit, 8) if signal.take_profit is not None else None,
            risk_amount=round(risk_amount, 8),
            fee_paid_entry=round(fee_paid_entry, 8),
            entry_reason=signal.reasons,
            score=signal.score,
            metadata={**signal.metadata, "position_size_multiplier": round(position_size_multiplier, 8)},
        )

    def mark_to_market(self, trade: SimulatedTrade, candle: HistoricalCandle):
        current_price = candle.close
        trade.gross_pnl = round(self._gross_pnl(trade, current_price), 8)
        trade.net_pnl = round(trade.gross_pnl - trade.fee_paid_entry, 8)

    def try_close_trade(self, trade: SimulatedTrade, candle: HistoricalCandle) -> bool:
        stop_hit = self._stop_hit(trade, candle)
        take_profit_hit = self._take_profit_hit(trade, candle)

        if stop_hit:
            exit_price = self._apply_exit_costs(trade.stop_loss, trade.side)
            self._close_trade(trade, candle.timestamp, exit_price, "stop_loss")
            return True

        if take_profit_hit and trade.take_profit is not None:
            exit_price = self._apply_exit_costs(trade.take_profit, trade.side)
            self._close_trade(trade, candle.timestamp, exit_price, "take_profit")
            return True

        self.mark_to_market(trade, candle)
        return False

    def _close_trade(self, trade: SimulatedTrade, timestamp: str, exit_price: float, reason: str):
        trade.status = "CLOSED"
        trade.exit_timestamp = timestamp
        trade.exit_price = round(exit_price, 8)
        trade.gross_pnl = round(self._gross_pnl(trade, exit_price), 8)
        trade.fee_paid_exit = round(exit_price * trade.quantity * self.fee_rate, 8)
        trade.net_pnl = round(trade.gross_pnl - trade.fee_paid_entry - trade.fee_paid_exit, 8)
        trade.exit_reason = reason

    def _gross_pnl(self, trade: SimulatedTrade, exit_price: float) -> float:
        if trade.side == "long":
            return (exit_price - trade.entry_price) * trade.quantity
        return (trade.entry_price - exit_price) * trade.quantity

    def _apply_entry_costs(self, base_price: float, side: str) -> float:
        spread_factor = self.spread_bps / 10000.0
        slippage_factor = self.slippage_bps / 10000.0
        if side == "long":
            return base_price * (1.0 + spread_factor + slippage_factor)
        return base_price * (1.0 - spread_factor - slippage_factor)

    def _apply_exit_costs(self, base_price: float, side: str) -> float:
        spread_factor = self.spread_bps / 10000.0
        slippage_factor = self.slippage_bps / 10000.0
        if side == "long":
            return base_price * (1.0 - spread_factor - slippage_factor)
        return base_price * (1.0 + spread_factor + slippage_factor)

    def _stop_hit(self, trade: SimulatedTrade, candle: HistoricalCandle) -> bool:
        if trade.side == "long":
            return candle.low <= trade.stop_loss
        return candle.high >= trade.stop_loss

    def _take_profit_hit(self, trade: SimulatedTrade, candle: HistoricalCandle) -> bool:
        if trade.take_profit is None:
            return False
        if trade.side == "long":
            return candle.high >= trade.take_profit
        return candle.low <= trade.take_profit
