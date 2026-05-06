from typing import List, Optional

from core.execution_simulator import BacktestSignal, HistoricalCandle


def generate_signal(candles: List[HistoricalCandle], index: int) -> Optional[BacktestSignal]:
    if index % 6 != 0:
        return None

    price = candles[index].close
    return BacktestSignal(
        asset="BTCUSDT",
        side="long",
        score=78.0,
        entry_reference_price=price,
        stop_loss=round(price - 2.0, 8),
        take_profit=round(price + 4.0, 8),
        reasons=["sample_backtest_signal"],
    )
