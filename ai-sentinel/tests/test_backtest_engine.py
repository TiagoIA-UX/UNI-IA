import sys
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.backtest_engine import BacktestEngine
from core.execution_simulator import BacktestSignal, HistoricalCandle
from core.risk_filter import RiskFilter
from core.signal_provider import MarketData, Signal
from core.system_state import SystemStatus, UniIAMode


class BacktestEngineTests(unittest.TestCase):
    def setUp(self):
        self.candles = [
            HistoricalCandle(timestamp="2026-01-01T00:00:00Z", open=100, high=101, low=99, close=100, volume=10),
            HistoricalCandle(timestamp="2026-01-01T01:00:00Z", open=100, high=104, low=99, close=103, volume=10),
            HistoricalCandle(timestamp="2026-01-01T02:00:00Z", open=103, high=108, low=102, close=107, volume=10),
            HistoricalCandle(timestamp="2026-01-01T03:00:00Z", open=107, high=109, low=106, close=108, volume=10),
        ]

    def test_runs_and_exports_deterministic_backtest(self):
        def signal_provider(candles, index):
            if index == 0:
                return BacktestSignal(
                    asset="BTCUSDT",
                    side="long",
                    score=88,
                    entry_reference_price=candles[index].close,
                    stop_loss=98,
                    take_profit=107,
                    reasons=["trend_filter_ok", "score_ok"],
                )
            return None

        engine = BacktestEngine(asset="BTCUSDT", signal_provider=signal_provider)
        result = engine.run(self.candles)

        self.assertEqual(result.asset, "BTCUSDT")
        self.assertEqual(result.metrics.total_trades, 1)
        self.assertGreaterEqual(result.metrics.wins, 0)
        self.assertTrue(result.decisions)
        self.assertEqual(result.governance.total_signals, 1)
        self.assertEqual(result.governance.signals_blocked_by_risk, 0)
        self.assertEqual(result.governance.signals_reduced_by_risk, 0)

        temp_dir = ROOT_DIR / "tests" / "_exports"
        with patch("pathlib.Path.mkdir") as mkdir_mock, patch("pathlib.Path.open", mock_open()), patch(
            "pathlib.Path.write_text"
        ) as write_text_mock:
            engine.export(result, temp_dir)

        mkdir_mock.assert_called_once()
        self.assertEqual(write_text_mock.call_count, 2)

    def test_accepts_formal_signal_provider_contract(self):
        class FakeProvider:
            def generate(self, market_data: MarketData):
                if market_data.index == 0:
                    return Signal(
                        asset=market_data.asset,
                        side="long",
                        score=80,
                        stop_loss=98,
                        take_profit=107,
                        entry_reference_price=market_data.current_candle.close,
                        reasons=["contract_ok"],
                    )
                return None

        engine = BacktestEngine(asset="BTCUSDT", signal_provider=FakeProvider())
        result = engine.run(self.candles)
        self.assertEqual(result.metrics.total_trades, 1)

    def test_applies_risk_filter_reduced_size_before_execution(self):
        class FakeProvider:
            def generate(self, market_data: MarketData):
                if market_data.index == 0:
                    return Signal(
                        asset=market_data.asset,
                        side="long",
                        score=80,
                        stop_loss=98,
                        take_profit=107,
                        entry_reference_price=market_data.current_candle.close,
                        reasons=["contract_ok"],
                    )
                return None

        risk_filter = RiskFilter(
            system_mode=UniIAMode.APPROVAL,
            system_status=SystemStatus.READY,
            approval_size_multiplier=0.5,
        )
        engine = BacktestEngine(asset="BTCUSDT", signal_provider=FakeProvider(), risk_filter=risk_filter)
        result = engine.run(self.candles)

        self.assertEqual(result.metrics.total_trades, 1)
        self.assertEqual(result.trades[0].risk_amount, 50.0)
        self.assertEqual(result.governance.total_signals, 1)
        self.assertEqual(result.governance.signals_reduced_by_risk, 1)
        self.assertEqual(result.governance.discipline_ratio, 1.0)
        self.assertTrue(any(item["decision"] == "risk_reduced_size" for item in result.decisions))

    def test_blocks_signal_when_risk_filter_blocks_system(self):
        class FakeProvider:
            def generate(self, market_data: MarketData):
                if market_data.index == 0:
                    return Signal(
                        asset=market_data.asset,
                        side="long",
                        score=80,
                        stop_loss=98,
                        take_profit=107,
                        entry_reference_price=market_data.current_candle.close,
                        reasons=["contract_ok"],
                    )
                return None

        risk_filter = RiskFilter(system_mode=UniIAMode.LIVE, system_status=SystemStatus.HALTED)
        engine = BacktestEngine(asset="BTCUSDT", signal_provider=FakeProvider(), risk_filter=risk_filter)
        result = engine.run(self.candles)

        self.assertEqual(result.metrics.total_trades, 0)
        self.assertEqual(result.governance.total_signals, 1)
        self.assertEqual(result.governance.signals_blocked_by_risk, 1)
        self.assertEqual(result.governance.discipline_ratio, 1.0)
        self.assertEqual(result.governance.capital_protected_estimate, 100.0)
        self.assertTrue(any(item["decision"] == "risk_blocked_system" for item in result.decisions))

    def test_tracks_governance_counters_and_ratio_across_multiple_signals(self):
        class SequencedProvider:
            def generate(self, market_data: MarketData):
                if market_data.index in {0, 1, 2}:
                    return Signal(
                        asset=market_data.asset,
                        side="long",
                        score=80,
                        stop_loss=98,
                        take_profit=107,
                        entry_reference_price=market_data.current_candle.close,
                        reasons=["contract_ok"],
                    )
                return None

        class SequencedRiskFilter:
            def __init__(self):
                self.actions = [
                    ("rejected", 0.0),
                    ("rejected", 0.0),
                    ("reduced_size", 0.5),
                ]
                self.index = 0

            def evaluate(self, portfolio_state, signal):
                from core.risk_filter import RiskDecision, RiskDecisionAction

                action_name, multiplier = self.actions[self.index]
                self.index += 1
                return RiskDecision(
                    action=RiskDecisionAction(action_name),
                    reasons=[f"test_{action_name}"],
                    size_multiplier=multiplier,
                )

            def notify_trade_closed(self, trade):
                return None

        candles = [
            HistoricalCandle(timestamp="2026-01-01T00:00:00Z", open=100, high=101, low=99, close=100, volume=10),
            HistoricalCandle(timestamp="2026-01-01T01:00:00Z", open=100, high=101, low=99, close=100, volume=10),
            HistoricalCandle(timestamp="2026-01-01T02:00:00Z", open=100, high=101, low=99, close=100, volume=10),
            HistoricalCandle(timestamp="2026-01-01T03:00:00Z", open=100, high=101, low=99, close=100, volume=10),
            HistoricalCandle(timestamp="2026-01-01T04:00:00Z", open=100, high=101, low=99, close=100, volume=10),
        ]
        engine = BacktestEngine(
            asset="BTCUSDT",
            signal_provider=SequencedProvider(),
            risk_filter=SequencedRiskFilter(),
        )

        result = engine.run(candles)

        self.assertEqual(result.governance.total_signals, 3)
        self.assertEqual(result.governance.signals_blocked_by_risk, 2)
        self.assertEqual(result.governance.signals_reduced_by_risk, 1)
        self.assertEqual(result.governance.discipline_ratio, 1.0)
        self.assertEqual(result.governance.capital_protected_estimate, 200.0)


if __name__ == "__main__":
    unittest.main()
