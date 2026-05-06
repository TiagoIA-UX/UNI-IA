import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from adapters.strategy_engine_adapter import StrategyEngineSignalProvider
from core.execution_simulator import HistoricalCandle
from core.signal_provider import MarketData


class StrategyEngineAdapterTests(unittest.TestCase):
    def test_generates_structured_signal_from_market_data(self):
        candles = []
        price = 100.0
        for idx in range(30):
            candles.append(
                HistoricalCandle(
                    timestamp=f"2026-01-01T{idx:02d}:00:00Z",
                    open=price,
                    high=price + 2.0,
                    low=price - 1.0,
                    close=price + 1.0,
                    volume=10.0,
                )
            )
            price += 1.0

        with patch.dict(os.environ, {"BACKTEST_MIN_SCORE": "60"}, clear=False):
            provider = StrategyEngineSignalProvider()
            signal = provider.generate(MarketData(asset="BTCUSDT", candles=candles, index=len(candles) - 1))

        self.assertIsNotNone(signal)
        self.assertEqual(signal.asset, "BTCUSDT")
        self.assertIn(signal.side, {"long", "short"})
        self.assertGreaterEqual(signal.score, 60.0)
        self.assertTrue(signal.reasons)


if __name__ == "__main__":
    unittest.main()
