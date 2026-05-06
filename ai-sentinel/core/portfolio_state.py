from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SimulatedTrade:
    trade_id: str
    asset: str
    side: str
    status: str
    entry_timestamp: str
    entry_price: float
    quantity: float
    stop_loss: float
    take_profit: Optional[float]
    risk_amount: float
    fee_paid_entry: float
    entry_reason: List[str] = field(default_factory=list)
    score: float = 0.0
    exit_timestamp: Optional[str] = None
    exit_price: Optional[float] = None
    fee_paid_exit: float = 0.0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    exit_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_open(self) -> bool:
        return self.status in {"PENDING", "OPEN", "PARTIAL"}


@dataclass
class PortfolioSnapshot:
    timestamp: str
    cash: float
    equity: float
    peak_equity: float
    drawdown: float
    drawdown_pct: float
    open_trade_id: Optional[str] = None


@dataclass
class PortfolioState:
    initial_capital: float
    max_drawdown_pct_limit: float = 20.0
    cash: float = field(init=False)
    realized_pnl: float = field(default=0.0, init=False)
    peak_equity: float = field(init=False)
    max_drawdown: float = field(default=0.0, init=False)
    max_drawdown_pct: float = field(default=0.0, init=False)
    blocked: bool = field(default=False, init=False)
    block_reason: Optional[str] = field(default=None, init=False)
    equity_curve: List[PortfolioSnapshot] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.cash = self.initial_capital
        self.peak_equity = self.initial_capital

    def apply_closed_trade(self, trade: SimulatedTrade):
        self.cash += trade.net_pnl
        self.realized_pnl += trade.net_pnl
        self.record_snapshot(trade.exit_timestamp or trade.entry_timestamp, open_trade=None)

    def record_snapshot(self, timestamp: str, open_trade: Optional[SimulatedTrade]):
        unrealized = 0.0
        if open_trade and open_trade.is_open():
            unrealized = open_trade.net_pnl

        equity = self.cash + unrealized
        if equity > self.peak_equity:
            self.peak_equity = equity

        drawdown = self.peak_equity - equity
        drawdown_pct = (drawdown / self.peak_equity * 100.0) if self.peak_equity > 0 else 0.0

        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        if drawdown_pct > self.max_drawdown_pct:
            self.max_drawdown_pct = drawdown_pct

        if drawdown_pct >= self.max_drawdown_pct_limit:
            self.blocked = True
            self.block_reason = f"max_drawdown_pct_limit_exceeded:{drawdown_pct:.2f}"

        self.equity_curve.append(
            PortfolioSnapshot(
                timestamp=timestamp,
                cash=round(self.cash, 8),
                equity=round(equity, 8),
                peak_equity=round(self.peak_equity, 8),
                drawdown=round(drawdown, 8),
                drawdown_pct=round(drawdown_pct, 4),
                open_trade_id=open_trade.trade_id if open_trade and open_trade.is_open() else None,
            )
        )

