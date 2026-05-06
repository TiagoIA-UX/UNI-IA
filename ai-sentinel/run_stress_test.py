import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.backtest_engine import BacktestEngine, BacktestResult, load_candles_from_csv
from core.execution_simulator import ExecutionSimulator
from core.portfolio_state import PortfolioState
from core.risk_filter import RiskFilter
from run_backtest import load_signal_provider


DRAWDOWN_REDUCTION_THRESHOLD_PCT = 20.0
NET_PROFIT_MAX_DECLINE_PCT = 10.0


def _pct_delta(new_value: float, reference_value: float) -> float:
    if reference_value == 0:
        return 0.0 if new_value == 0 else 100.0
    return ((new_value - reference_value) / abs(reference_value)) * 100.0


def _drawdown_reduction_pct(risk_on_drawdown_pct: float, risk_off_drawdown_pct: float) -> float:
    if risk_off_drawdown_pct <= 0:
        return 0.0
    return ((risk_off_drawdown_pct - risk_on_drawdown_pct) / risk_off_drawdown_pct) * 100.0


def classify_comparison(*, drawdown_reduction_pct: float, net_profit_delta_pct: float) -> str:
    if (
        drawdown_reduction_pct >= DRAWDOWN_REDUCTION_THRESHOLD_PCT
        and net_profit_delta_pct >= -NET_PROFIT_MAX_DECLINE_PCT
    ):
        return "RISK_FILTER_PROTECTIVE"
    if drawdown_reduction_pct < 0 or net_profit_delta_pct < -NET_PROFIT_MAX_DECLINE_PCT:
        return "DETRIMENTAL"
    return "NEUTRAL"


def run_scenario(
    *,
    asset: str,
    candles,
    signal_provider,
    risk_filter,
) -> BacktestResult:
    engine = BacktestEngine(
        asset=asset,
        signal_provider=signal_provider,
        execution_simulator=ExecutionSimulator(),
        portfolio_state=PortfolioState(initial_capital=10000.0, max_drawdown_pct_limit=20.0),
        risk_filter=risk_filter,
    )
    return engine.run(candles)


def build_report(
    *,
    dataset: str,
    strategy: str,
    result_on: BacktestResult,
    result_off: BacktestResult,
    initial_capital: float,
):
    drawdown_reduction_pct = _drawdown_reduction_pct(
        result_on.metrics.max_drawdown_pct,
        result_off.metrics.max_drawdown_pct,
    )
    net_profit_delta_pct = _pct_delta(result_on.metrics.net_profit, result_off.metrics.net_profit)
    classification = classify_comparison(
        drawdown_reduction_pct=drawdown_reduction_pct,
        net_profit_delta_pct=net_profit_delta_pct,
    )

    return {
        "experiment": {
            "dataset": dataset,
            "strategy": strategy,
            "capital_initial": initial_capital,
            "criteria": {
                "drawdown_reduction_threshold_pct": DRAWDOWN_REDUCTION_THRESHOLD_PCT,
                "net_profit_max_decline_pct": NET_PROFIT_MAX_DECLINE_PCT,
            },
        },
        "scenario_A": {
            "risk_filter": "ON",
            "metrics": asdict(result_on.metrics),
            "governance": asdict(result_on.governance),
        },
        "scenario_B": {
            "risk_filter": "OFF",
            "metrics": asdict(result_off.metrics),
            "governance": asdict(result_off.governance),
        },
        "comparison": {
            "drawdown_delta_pct": round(_pct_delta(result_on.metrics.max_drawdown_pct, result_off.metrics.max_drawdown_pct), 4),
            "drawdown_reduction_pct": round(drawdown_reduction_pct, 4),
            "net_profit_delta_pct": round(net_profit_delta_pct, 4),
            "capital_protected": round(result_on.governance.capital_protected_estimate, 8),
            "classification": classification,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Executa stress test comparativo da UNI IA com RiskFilter ON/OFF.")
    parser.add_argument("--asset", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--output-dir", default="stress_test_output")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candles = load_candles_from_csv(csv_path)
    signal_provider = load_signal_provider(args.strategy)

    result_on = run_scenario(
        asset=args.asset,
        candles=candles,
        signal_provider=signal_provider,
        risk_filter=RiskFilter(max_consecutive_losses=2, max_drawdown_pct=20.0),
    )
    result_off = run_scenario(
        asset=args.asset,
        candles=candles,
        signal_provider=signal_provider,
        risk_filter=None,
    )

    report = build_report(
        dataset=csv_path.name,
        strategy=args.strategy,
        result_on=result_on,
        result_off=result_off,
        initial_capital=10000.0,
    )

    (output_dir / "stress_test_report.json").write_text(
        json.dumps(report, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
