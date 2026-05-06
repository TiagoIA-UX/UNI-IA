from typing import List, Optional

from core.execution_simulator import BacktestSignal, HistoricalCandle


def generate_signal(candles: List[HistoricalCandle], index: int) -> Optional[BacktestSignal]:
    if index % 2 != 0:
        return None

    price = candles[index].close
    return BacktestSignal(
        asset="BTCUSDT",
        side="long",
        score=81.0,
        entry_reference_price=price,
        stop_loss=round(price - 1.0, 8),
        take_profit=round(price + 3.0, 8),
        reasons=["stress_test_long_signal"],
    )
