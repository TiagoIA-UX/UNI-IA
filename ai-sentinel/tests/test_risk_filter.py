import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.portfolio_state import PortfolioState, SimulatedTrade
from core.risk_filter import RiskDecisionAction, RiskFilter
from core.signal_provider import Signal
from core.system_state import SystemStatus, UniIAMode


def _build_signal():
    return Signal(
        asset="BTCUSDT",
        side="long",
        score=82.0,
        stop_loss=98.0,
        take_profit=105.0,
        entry_reference_price=100.0,
        reasons=["test_signal"],
    )


def _build_trade(net_pnl: float) -> SimulatedTrade:
    return SimulatedTrade(
        trade_id="trade-1",
        asset="BTCUSDT",
        side="long",
        status="CLOSED",
        entry_timestamp="2026-01-01T00:00:00Z",
        entry_price=100.0,
        quantity=1.0,
        stop_loss=98.0,
        take_profit=105.0,
        risk_amount=100.0,
        fee_paid_entry=0.0,
        exit_timestamp="2026-01-01T01:00:00Z",
        exit_price=99.0,
        net_pnl=net_pnl,
    )


class RiskFilterTests(unittest.TestCase):
    def test_blocks_when_system_is_halted(self):
        portfolio = PortfolioState(initial_capital=10000.0)
        risk_filter = RiskFilter(system_mode=UniIAMode.LIVE, system_status=SystemStatus.HALTED)

        decision = risk_filter.evaluate(portfolio, _build_signal())

        self.assertEqual(decision.action, RiskDecisionAction.BLOCKED_SYSTEM)

    def test_reduces_size_in_approval_mode(self):
        portfolio = PortfolioState(initial_capital=10000.0)
        risk_filter = RiskFilter(
            system_mode=UniIAMode.APPROVAL,
            system_status=SystemStatus.READY,
            approval_size_multiplier=0.4,
        )

        decision = risk_filter.evaluate(portfolio, _build_signal())

        self.assertEqual(decision.action, RiskDecisionAction.REDUCED_SIZE)
        self.assertEqual(decision.size_multiplier, 0.4)

    def test_rejects_after_loss_streak_limit(self):
        portfolio = PortfolioState(initial_capital=10000.0)
        risk_filter = RiskFilter(
            system_mode=UniIAMode.PAPER,
            system_status=SystemStatus.READY,
            max_consecutive_losses=2,
        )
        risk_filter.notify_trade_closed(_build_trade(net_pnl=-10.0))
        risk_filter.notify_trade_closed(_build_trade(net_pnl=-5.0))

        decision = risk_filter.evaluate(portfolio, _build_signal())

        self.assertEqual(decision.action, RiskDecisionAction.REJECTED)
        self.assertIn("loss_streak_limit_reached:2", decision.reasons)


if __name__ == "__main__":
    unittest.main()
