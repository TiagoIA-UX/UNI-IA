import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.daily_ops_report import DailyOpsReportService


def main():
    parser = argparse.ArgumentParser(description="Gera relatorio operacional diario da UNI IA.")
    parser.add_argument("--date", default=None, help="Data UTC no formato YYYY-MM-DD. Default: hoje (UTC)")
    parser.add_argument("--output", default=None, help="Arquivo de saida JSON opcional")
    args = parser.parse_args()

    report_date = None
    if args.date:
        report_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    service = DailyOpsReportService()
    report = service.generate_daily_report(report_date=report_date)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
