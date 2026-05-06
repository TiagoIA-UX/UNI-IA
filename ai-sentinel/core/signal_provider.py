from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from core.execution_simulator import HistoricalCandle


@dataclass
class Signal:
    asset: str
    side: str
    score: float
    stop_loss: float
    take_profit: Optional[float] = None
    entry_reference_price: Optional[float] = None
    position_size_multiplier: float = 1.0
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketData:
    asset: str
    candles: List[HistoricalCandle]
    index: int

    @property
    def current_candle(self) -> HistoricalCandle:
        return self.candles[self.index]

    @property
    def window(self) -> List[HistoricalCandle]:
        return self.candles[: self.index + 1]


class SignalProvider(Protocol):
    def generate(self, market_data: MarketData) -> Optional[Signal]:
        ...
