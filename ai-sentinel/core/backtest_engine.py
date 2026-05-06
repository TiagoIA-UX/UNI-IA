import csv
import json
import math
import os
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Callable, Dict, List, Optional

from core.execution_simulator import BacktestSignal, ExecutionSimulator, HistoricalCandle
from core.portfolio_state import PortfolioState, SimulatedTrade
from core.risk_filter import RiskDecision, RiskDecisionAction, RiskFilter
from core.signal_provider import MarketData, Signal, SignalProvider


LegacySignalProvider = Callable[[List[HistoricalCandle], int], Optional[BacktestSignal]]


@dataclass
class BacktestMetrics:
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    profit_factor: float
    avg_rr: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    expectancy: float
    longest_losing_streak: int
    net_profit: float


@dataclass
class GovernanceMetrics:
    total_signals: int = 0
    signals_blocked_by_risk: int = 0
    signals_reduced_by_risk: int = 0
    discipline_ratio: float = 0.0
    capital_protected_estimate: float = 0.0


@dataclass
class BacktestResult:
    asset: str
    metrics: BacktestMetrics
    governance: GovernanceMetrics
    trades: List[SimulatedTrade] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)


class BacktestEngine:
    def __init__(
        self,
        *,
        asset: str,
        signal_provider: SignalProvider | LegacySignalProvider,
        execution_simulator: Optional[ExecutionSimulator] = None,
        portfolio_state: Optional[PortfolioState] = None,
        risk_filter: Optional[RiskFilter] = None,
    ):
        self.asset = asset
        self.signal_provider = signal_provider
        self.execution = execution_simulator or ExecutionSimulator()
        self.portfolio = portfolio_state or PortfolioState(
            initial_capital=float(os.getenv("BACKTEST_INITIAL_CAPITAL", "10000")),
            max_drawdown_pct_limit=float(os.getenv("BACKTEST_MAX_DRAWDOWN_PCT_LIMIT", "20")),
        )
        self.risk_filter = risk_filter
        self.trades: List[SimulatedTrade] = []
        self.decisions: List[Dict[str, Any]] = []
        self.governance = GovernanceMetrics()

    def run(self, candles: List[HistoricalCandle]) -> BacktestResult:
        if len(candles) < 2:
            raise RuntimeError("Backtest exige ao menos 2 candles.")

        open_trade: Optional[SimulatedTrade] = None
        pending_signal: Optional[BacktestSignal] = None

        for index, candle in enumerate(candles):
            if self.portfolio.blocked:
                self._record_decision(
                    candle.timestamp,
                    "blocked",
                    {
                        "reason": self.portfolio.block_reason,
                        "open_trade_id": open_trade.trade_id if open_trade else None,
                    },
                )
                break

            if pending_signal is not None:
                open_trade = self.execution.open_trade(pending_signal, candle, self.portfolio.cash)
                self._record_decision(
                    candle.timestamp,
                    "opened_trade",
                    {
                        "trade_id": open_trade.trade_id,
                        "side": open_trade.side,
                        "entry_price": open_trade.entry_price,
                        "stop_loss": open_trade.stop_loss,
                        "take_profit": open_trade.take_profit,
                    },
                )
                pending_signal = None

            if open_trade is not None and open_trade.is_open():
                was_closed = self.execution.try_close_trade(open_trade, candle)
                self.portfolio.record_snapshot(candle.timestamp, open_trade)
                if was_closed:
                    self.portfolio.apply_closed_trade(open_trade)
                    if self.risk_filter is not None:
                        self.risk_filter.notify_trade_closed(open_trade)
                    self.trades.append(open_trade)
                    self._record_decision(
                        candle.timestamp,
                        "closed_trade",
                        {
                            "trade_id": open_trade.trade_id,
                            "exit_reason": open_trade.exit_reason,
                            "net_pnl": open_trade.net_pnl,
                        },
                    )
                    open_trade = None

            if open_trade is None and index < len(candles) - 1:
                signal = self._generate_signal(candles, index)
                if signal:
                    self.governance.total_signals += 1
                    signal, blocked = self._evaluate_risk(candle.timestamp, signal)
                    if blocked:
                        break
                    if signal is None:
                        continue
                    pending_signal = signal
                    self._record_decision(
                        candle.timestamp,
                        "generated_signal",
                        {
                            "side": signal.side,
                            "score": signal.score,
                            "stop_loss": signal.stop_loss,
                            "take_profit": signal.take_profit,
                        },
                    )
                else:
                    self._record_decision(candle.timestamp, "no_signal", {})

        if open_trade is not None and open_trade.is_open():
            last_candle = candles[-1]
            self.execution.mark_to_market(open_trade, last_candle)
            open_trade.status = "CANCELLED"
            open_trade.exit_timestamp = last_candle.timestamp
            open_trade.exit_price = last_candle.close
            open_trade.exit_reason = "end_of_backtest"
            open_trade.fee_paid_exit = 0.0
            open_trade.net_pnl = round(open_trade.net_pnl, 8)
            self.portfolio.apply_closed_trade(open_trade)
            if self.risk_filter is not None:
                self.risk_filter.notify_trade_closed(open_trade)
            self.trades.append(open_trade)

        metrics = self._calculate_metrics()
        return BacktestResult(
            asset=self.asset,
            metrics=metrics,
            governance=self._calculate_governance_metrics(),
            trades=self.trades,
            decisions=self.decisions,
            equity_curve=[asdict(item) for item in self.portfolio.equity_curve],
        )

    def export(self, result: BacktestResult, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)

        trades_path = output_dir / "trades.csv"
        equity_path = output_dir / "equity_curve.csv"
        decisions_path = output_dir / "decisions.json"
        summary_path = output_dir / "summary.json"

        with trades_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(asdict(result.trades[0]).keys()) if result.trades else ["trade_id"])
            writer.writeheader()
            for trade in result.trades:
                writer.writerow(asdict(trade))

        with equity_path.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = list(result.equity_curve[0].keys()) if result.equity_curve else ["timestamp"]
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in result.equity_curve:
                writer.writerow(row)

        decisions_path.write_text(json.dumps(result.decisions, ensure_ascii=True, indent=2), encoding="utf-8")
        summary_path.write_text(
            json.dumps(
                {
                    "asset": result.asset,
                    "metrics": asdict(result.metrics),
                    "governance": asdict(result.governance),
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _record_decision(self, timestamp: str, decision: str, payload: Dict[str, Any]):
        self.decisions.append(
            {
                "timestamp": timestamp,
                "decision": decision,
                "asset": self.asset,
                "payload": payload,
            }
        )

    def _generate_signal(self, candles: List[HistoricalCandle], index: int) -> Optional[BacktestSignal]:
        if hasattr(self.signal_provider, "generate"):
            signal = self.signal_provider.generate(MarketData(asset=self.asset, candles=candles, index=index))
        else:
            signal = self.signal_provider(candles, index)

        if signal is None:
            return None

        if isinstance(signal, BacktestSignal):
            return signal

        if isinstance(signal, Signal):
            return BacktestSignal(
                asset=signal.asset,
                side=signal.side,
                score=signal.score,
                entry_reference_price=signal.entry_reference_price or candles[index].close,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                position_size_multiplier=signal.position_size_multiplier,
                reasons=signal.reasons,
                metadata=signal.metadata,
            )

        raise RuntimeError(f"Tipo de sinal invalido no backtest: {type(signal).__name__}")

    def _evaluate_risk(self, timestamp: str, signal: BacktestSignal) -> tuple[Optional[BacktestSignal], bool]:
        if self.risk_filter is None:
            return signal, False

        risk_signal = Signal(
            asset=signal.asset,
            side=signal.side,
            score=signal.score,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            entry_reference_price=signal.entry_reference_price,
            position_size_multiplier=signal.position_size_multiplier,
            reasons=list(signal.reasons),
            metadata=dict(signal.metadata),
        )
        decision = self.risk_filter.evaluate(self.portfolio, risk_signal)
        self._record_risk_decision(timestamp, decision)
        self._record_governance_decision(decision)

        if decision.action == RiskDecisionAction.BLOCKED_SYSTEM:
            return None, True
        if decision.action == RiskDecisionAction.REJECTED:
            return None, False
        if decision.action == RiskDecisionAction.REDUCED_SIZE:
            adjusted_multiplier = max(signal.position_size_multiplier * decision.size_multiplier, 0.0)
            return replace(signal, position_size_multiplier=adjusted_multiplier), False
        return signal, False

    def _record_risk_decision(self, timestamp: str, decision: RiskDecision):
        self._record_decision(
            timestamp,
            f"risk_{decision.action.value}",
            {
                "reasons": decision.reasons,
                "size_multiplier": round(decision.size_multiplier, 8),
            },
        )

    def _record_governance_decision(self, decision: RiskDecision):
        if decision.action in {RiskDecisionAction.REJECTED, RiskDecisionAction.BLOCKED_SYSTEM}:
            self.governance.signals_blocked_by_risk += 1
            self.governance.capital_protected_estimate += self._theoretical_risk_amount()
            return

        if decision.action == RiskDecisionAction.REDUCED_SIZE:
            self.governance.signals_reduced_by_risk += 1

    def _calculate_governance_metrics(self) -> GovernanceMetrics:
        total_signals = self.governance.total_signals
        interventions = self.governance.signals_blocked_by_risk + self.governance.signals_reduced_by_risk
        discipline_ratio = (interventions / total_signals) if total_signals else 0.0
        return GovernanceMetrics(
            total_signals=total_signals,
            signals_blocked_by_risk=self.governance.signals_blocked_by_risk,
            signals_reduced_by_risk=self.governance.signals_reduced_by_risk,
            discipline_ratio=round(discipline_ratio, 4),
            capital_protected_estimate=round(self.governance.capital_protected_estimate, 8),
        )

    def _theoretical_risk_amount(self) -> float:
        return max(self.portfolio.cash * (self.execution.risk_per_trade_pct / 100.0), 0.0)

    def _calculate_metrics(self) -> BacktestMetrics:
        total_trades = len(self.trades)
        wins = sum(1 for trade in self.trades if trade.net_pnl > 0)
        losses = sum(1 for trade in self.trades if trade.net_pnl < 0)
        win_rate = (wins / total_trades * 100.0) if total_trades else 0.0

        gross_profit = sum(trade.net_pnl for trade in self.trades if trade.net_pnl > 0)
        gross_loss = abs(sum(trade.net_pnl for trade in self.trades if trade.net_pnl < 0))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0

        rr_values = []
        for trade in self.trades:
            if trade.risk_amount > 0:
                rr_values.append(trade.net_pnl / trade.risk_amount)
        avg_rr = mean(rr_values) if rr_values else 0.0

        pnl_values = [trade.net_pnl for trade in self.trades]
        avg_win = mean([value for value in pnl_values if value > 0]) if wins else 0.0
        avg_loss = abs(mean([value for value in pnl_values if value < 0])) if losses else 0.0
        loss_rate = 1.0 - (wins / total_trades) if total_trades else 0.0
        expectancy = ((wins / total_trades) * avg_win - loss_rate * avg_loss) if total_trades else 0.0

        longest_losing_streak = 0
        current_streak = 0
        for trade in self.trades:
            if trade.net_pnl < 0:
                current_streak += 1
                longest_losing_streak = max(longest_losing_streak, current_streak)
            else:
                current_streak = 0

        sharpe_ratio = 0.0
        if len(pnl_values) > 1 and pstdev(pnl_values) > 0:
            sharpe_ratio = mean(pnl_values) / pstdev(pnl_values) * math.sqrt(len(pnl_values))

        return BacktestMetrics(
            total_trades=total_trades,
            wins=wins,
            losses=losses,
            win_rate=round(win_rate, 4),
            profit_factor=round(profit_factor, 4) if math.isfinite(profit_factor) else profit_factor,
            avg_rr=round(avg_rr, 4),
            max_drawdown=round(self.portfolio.max_drawdown, 8),
            max_drawdown_pct=round(self.portfolio.max_drawdown_pct, 4),
            sharpe_ratio=round(sharpe_ratio, 4),
            expectancy=round(expectancy, 8),
            longest_losing_streak=longest_losing_streak,
            net_profit=round(sum(trade.net_pnl for trade in self.trades), 8),
        )


def load_candles_from_csv(csv_path: Path) -> List[HistoricalCandle]:
    candles: List[HistoricalCandle] = []
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            candles.append(
                HistoricalCandle(
                    timestamp=str(row["timestamp"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0.0) or 0.0),
                )
            )
    return candles
