import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.backtest_engine import BacktestEngine, load_candles_from_csv
from core.risk_filter import RiskFilter


def load_signal_provider(import_path: str):
    if ":" not in import_path:
        raise RuntimeError("Use --strategy module.submodule:function")
    module_name, func_name = import_path.split(":", 1)
    module = importlib.import_module(module_name)
    signal_provider = getattr(module, func_name, None)
    if signal_provider is None:
        raise RuntimeError(f"Strategy callable nao encontrada: {import_path}")
    return signal_provider


def main():
    parser = argparse.ArgumentParser(description="Executa backtest deterministico da UNI IA.")
    parser.add_argument("--asset", required=True, help="Ativo de referencia do backtest, ex: BTCUSDT")
    parser.add_argument("--csv", required=True, help="Arquivo CSV com timestamp,open,high,low,close,volume")
    parser.add_argument("--strategy", required=True, help="Import path no formato module:function")
    parser.add_argument("--output-dir", default="backtest_output", help="Diretorio de exportacao dos resultados")
    args = parser.parse_args()

    candles = load_candles_from_csv(Path(args.csv))
    signal_provider = load_signal_provider(args.strategy)

    engine = BacktestEngine(asset=args.asset, signal_provider=signal_provider, risk_filter=RiskFilter())
    result = engine.run(candles)
    output_dir = Path(args.output_dir)
    engine.export(result, output_dir)

    print(
        json.dumps(
            {
                "asset": result.asset,
                "metrics": result.metrics.__dict__,
                "output_dir": str(output_dir.resolve()),
            },
            ensure_ascii=True,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
