import os
from dataclasses import dataclass
from enum import Enum
from typing import List

from core.portfolio_state import PortfolioState, SimulatedTrade
from core.signal_provider import Signal
from core.system_state import SystemStatus, UniIAMode


class RiskDecisionAction(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REDUCED_SIZE = "reduced_size"
    BLOCKED_SYSTEM = "blocked_system"


@dataclass
class RiskDecision:
    action: RiskDecisionAction
    reasons: List[str]
    size_multiplier: float = 1.0


class RiskFilter:
    def __init__(
        self,
        *,
        base_risk_per_trade_pct: float | None = None,
        max_risk_per_trade_pct: float | None = None,
        max_drawdown_pct: float | None = None,
        max_consecutive_losses: int | None = None,
        degraded_size_multiplier: float | None = None,
        approval_size_multiplier: float | None = None,
        system_mode: UniIAMode = UniIAMode.PAPER,
        system_status: SystemStatus = SystemStatus.READY,
    ):
        self.base_risk_per_trade_pct = (
            base_risk_per_trade_pct
            if base_risk_per_trade_pct is not None
            else float(os.getenv("BACKTEST_RISK_PER_TRADE_PCT", "1.0"))
        )
        self.max_risk_per_trade_pct = (
            max_risk_per_trade_pct
            if max_risk_per_trade_pct is not None
            else float(os.getenv("BACKTEST_MAX_RISK_PER_TRADE_PCT", str(self.base_risk_per_trade_pct)))
        )
        self.max_drawdown_pct = (
            max_drawdown_pct
            if max_drawdown_pct is not None
            else float(os.getenv("BACKTEST_RISK_FILTER_MAX_DRAWDOWN_PCT", "20.0"))
        )
        self.max_consecutive_losses = (
            max_consecutive_losses
            if max_consecutive_losses is not None
            else int(os.getenv("BACKTEST_MAX_CONSECUTIVE_LOSSES", "3"))
        )
        self.degraded_size_multiplier = (
            degraded_size_multiplier
            if degraded_size_multiplier is not None
            else float(os.getenv("BACKTEST_DEGRADED_SIZE_MULTIPLIER", "0.5"))
        )
        self.approval_size_multiplier = (
            approval_size_multiplier
            if approval_size_multiplier is not None
            else float(os.getenv("BACKTEST_APPROVAL_SIZE_MULTIPLIER", "0.5"))
        )
        self.system_mode = system_mode
        self.system_status = system_status
        self.consecutive_losses = 0

    def evaluate(self, portfolio_state: PortfolioState, signal: Signal) -> RiskDecision:
        if self.system_status in {SystemStatus.LOCKED, SystemStatus.HALTED}:
            return RiskDecision(
                action=RiskDecisionAction.BLOCKED_SYSTEM,
                reasons=[f"system_status:{self.system_status.value}"],
                size_multiplier=0.0,
            )

        reasons: List[str] = []
        size_multiplier = max(float(signal.position_size_multiplier), 0.0)

        if portfolio_state.max_drawdown_pct >= self.max_drawdown_pct:
            reasons.append(f"drawdown_limit_reached:{portfolio_state.max_drawdown_pct:.4f}")

        if self.max_consecutive_losses >= 0 and self.consecutive_losses >= self.max_consecutive_losses:
            reasons.append(f"loss_streak_limit_reached:{self.consecutive_losses}")

        if reasons:
            return RiskDecision(
                action=RiskDecisionAction.REJECTED,
                reasons=reasons,
                size_multiplier=0.0,
            )

        capped_multiplier = self._cap_risk_multiplier(size_multiplier)
        if capped_multiplier < size_multiplier:
            reasons.append(f"risk_capped:{self.base_risk_per_trade_pct:.4f}->{self.max_risk_per_trade_pct:.4f}")
            size_multiplier = capped_multiplier

        mode_multiplier = self._mode_multiplier()
        if mode_multiplier < 1.0:
            adjusted_multiplier = min(size_multiplier, mode_multiplier)
            if adjusted_multiplier < size_multiplier:
                reasons.append(f"system_mode:{self.system_mode.value}")
                size_multiplier = adjusted_multiplier

        if reasons:
            return RiskDecision(
                action=RiskDecisionAction.REDUCED_SIZE,
                reasons=reasons,
                size_multiplier=round(size_multiplier, 8),
            )

        return RiskDecision(
            action=RiskDecisionAction.APPROVED,
            reasons=["risk_checks_passed"],
            size_multiplier=round(size_multiplier, 8),
        )

    def notify_trade_closed(self, trade: SimulatedTrade):
        if trade.net_pnl < 0:
            self.consecutive_losses += 1
            return
        self.consecutive_losses = 0

    def _cap_risk_multiplier(self, current_multiplier: float) -> float:
        if self.base_risk_per_trade_pct <= 0:
            return 0.0
        if self.max_risk_per_trade_pct <= 0:
            return 0.0
        max_multiplier = self.max_risk_per_trade_pct / self.base_risk_per_trade_pct
        return max(0.0, min(current_multiplier, max_multiplier))

    def _mode_multiplier(self) -> float:
        if self.system_status == SystemStatus.DEGRADED:
            return max(self.degraded_size_multiplier, 0.0)
        if self.system_mode == UniIAMode.APPROVAL:
            return max(self.approval_size_multiplier, 0.0)
        return 1.0
