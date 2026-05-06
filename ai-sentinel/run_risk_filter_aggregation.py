import argparse
import csv
import json
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple


ROOT_DIR = Path(__file__).resolve().parent
DOCS_OUTPUT = ROOT_DIR.parent / "docs" / "research" / "risk-filter-aggregation.json"
FRONTEND_OUTPUT = ROOT_DIR.parent / "zairyx-blog" / "lib" / "risk-filter-aggregation.json"
DEFAULT_REPORT_GLOB = "stress_test_output*/stress_test_report.json"
RISK_FILTER_VERSION = "v1"
SCHEMA_VERSION = 2

# Canonical metadata for institutional presentation and deterministic gates.
VERSION_METADATA: Dict[str, Dict[str, str]] = {
    "v1": {"regime": "Adverso descendente", "expected_classification": "RISK_FILTER_PROTECTIVE"},
    "v2": {"regime": "Tendencial favoravel", "expected_classification": "NEUTRAL"},
    "v3": {"regime": "Lateral com ruido", "expected_classification": "RISK_FILTER_PROTECTIVE"},
    "v4": {"regime": "Volatilidade extrema", "expected_classification": "RISK_FILTER_PROTECTIVE"},
}


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _sha256_text(content: str) -> str:
    return _sha256_bytes(content.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_csv_timestamps(csv_path: Path) -> List[datetime]:
    timestamps: List[datetime] = []
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            timestamps.append(datetime.fromisoformat(str(row["timestamp"]).replace("Z", "+00:00")))
    return timestamps


def _infer_timeframe(timestamps: List[datetime]) -> str:
    if len(timestamps) < 2:
        return "unknown"
    delta = timestamps[1] - timestamps[0]
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return "unknown"
    if seconds % 86400 == 0:
        return f"{seconds // 86400}d"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


def _series_duration_days(timestamps: List[datetime]) -> float:
    if len(timestamps) < 2:
        return 1.0
    delta = timestamps[1] - timestamps[0]
    return max((len(timestamps) * delta.total_seconds()) / 86400.0, 1 / 24.0)


def _classification_from_report(report: Dict[str, Any]) -> str:
    return str(report.get("comparison", {}).get("classification", "UNKNOWN"))


def _normalize_version(output_dir: Path) -> str:
    name = output_dir.name
    if name.endswith("_v2"):
        return "v2"
    if name.endswith("_v3"):
        return "v3"
    if name.endswith("_v4"):
        return "v4"
    return "v1"


def _dataset_to_csv_path(dataset: str) -> Path:
    return ROOT_DIR / "tests" / dataset


def _strategy_to_file_path(strategy: str) -> Path | None:
    module_part = strategy.split(":", 1)[0]
    candidate = ROOT_DIR / Path(*module_part.split("."))
    candidate = candidate.with_suffix(".py")
    return candidate if candidate.exists() else None


def build_series_record(report_path: Path) -> Dict[str, Any]:
    report = _load_json(report_path)
    output_dir = report_path.parent
    dataset = str(report["experiment"]["dataset"])
    csv_path = _dataset_to_csv_path(dataset)
    strategy_path = _strategy_to_file_path(str(report["experiment"]["strategy"]))
    timestamps = _read_csv_timestamps(csv_path)
    timeframe = _infer_timeframe(timestamps)
    duration_days = _series_duration_days(timestamps)

    scenario_a = report["scenario_A"]
    metrics = scenario_a["metrics"]
    governance = scenario_a["governance"]
    comparison = report["comparison"]
    criteria = report.get("experiment", {}).get("criteria", {})

    total_signals = int(governance["total_signals"])
    signals_blocked = int(governance["signals_blocked_by_risk"])
    signals_reduced = int(governance["signals_reduced_by_risk"])
    total_trades = int(metrics["total_trades"])

    raw_signals_per_day = round(total_signals / duration_days, 4)
    executed_signals_per_day = round(total_trades / duration_days, 4)

    return {
        "version": _normalize_version(output_dir),
        "regime": VERSION_METADATA.get(_normalize_version(output_dir), {}).get("regime", "Regime desconhecido"),
        "dataset": dataset,
        "dataset_sha256": _sha256_file(csv_path),
        "strategy": report["experiment"]["strategy"],
        "strategy_sha256": _sha256_file(strategy_path) if strategy_path else None,
        "mandate": "core",
        "day": timestamps[0].date().isoformat() if timestamps else None,
        "timeframe": timeframe,
        "classification": comparison["classification"],
        "criteria": {
            "drawdown_reduction_threshold_pct": float(criteria.get("drawdown_reduction_threshold_pct", 0.0)),
            "net_profit_max_decline_pct": float(criteria.get("net_profit_max_decline_pct", 0.0)),
        },
        "report_sha256": _sha256_file(report_path),
        "runner_sha256": _sha256_file(ROOT_DIR / "run_risk_filter_aggregation.py"),
        "period": {
            "start": timestamps[0].isoformat().replace("+00:00", "Z") if timestamps else None,
            "end": timestamps[-1].isoformat().replace("+00:00", "Z") if timestamps else None,
            "duration_days": round(duration_days, 6),
        },
        "signals": {
            "raw_total": total_signals,
            "blocked": signals_blocked,
            "reduced": signals_reduced,
            "executed": total_trades,
            "raw_per_day": raw_signals_per_day,
            "executed_per_day": executed_signals_per_day,
            "blocked_rate": round(signals_blocked / total_signals, 4) if total_signals else 0.0,
            "execution_rate": round(total_trades / total_signals, 4) if total_signals else 0.0,
        },
        "risk": {
            "drawdown_reduction_pct": float(comparison["drawdown_reduction_pct"]),
            "net_profit_delta_pct": float(comparison["net_profit_delta_pct"]),
            "capital_protected": float(comparison["capital_protected"]),
        },
        "metrics": {
            "net_profit": float(metrics["net_profit"]),
            "max_drawdown_pct": float(metrics["max_drawdown_pct"]),
            "discipline_ratio": float(governance["discipline_ratio"]),
        },
    }


def aggregate(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    def group_by(keys: Tuple[str, ...]) -> Dict[str, Dict[str, Any]]:
        grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[tuple(record[key] for key in keys)].append(record)

        output: Dict[str, Dict[str, Any]] = {}
        for key_tuple, items in grouped.items():
            label = "|".join(str(item) for item in key_tuple)
            output[label] = {
                "count": len(items),
                "raw_signals_per_day": round(mean(item["signals"]["raw_per_day"] for item in items), 4),
                "executed_signals_per_day": round(mean(item["signals"]["executed_per_day"] for item in items), 4),
                "blocked_rate": round(mean(item["signals"]["blocked_rate"] for item in items), 4),
                "execution_rate": round(mean(item["signals"]["execution_rate"] for item in items), 4),
                "drawdown_reduction_pct": round(mean(item["risk"]["drawdown_reduction_pct"] for item in items), 4),
                "net_profit_delta_pct": round(mean(item["risk"]["net_profit_delta_pct"] for item in items), 4),
                "capital_protected": round(sum(item["risk"]["capital_protected"] for item in items), 8),
            }
        return output

    overall = {
        "count": len(records),
        "raw_signals_per_day": round(mean(item["signals"]["raw_per_day"] for item in records), 4) if records else 0.0,
        "executed_signals_per_day": round(mean(item["signals"]["executed_per_day"] for item in records), 4) if records else 0.0,
        "blocked_rate": round(mean(item["signals"]["blocked_rate"] for item in records), 4) if records else 0.0,
        "execution_rate": round(mean(item["signals"]["execution_rate"] for item in records), 4) if records else 0.0,
        "drawdown_reduction_pct": round(mean(item["risk"]["drawdown_reduction_pct"] for item in records), 4) if records else 0.0,
        "net_profit_delta_pct": round(mean(item["risk"]["net_profit_delta_pct"] for item in records), 4) if records else 0.0,
        "capital_protected": round(sum(item["risk"]["capital_protected"] for item in records), 8),
    }

    return {
        "overall": overall,
        "by_day": group_by(("day",)),
        "by_classification": group_by(("classification",)),
        "by_timeframe": group_by(("timeframe",)),
        "by_mandate": group_by(("mandate",)),
        "by_version": group_by(("version",)),
        "by_strategy": group_by(("strategy",)),
        "by_day_classification": group_by(("day", "classification")),
        "by_timeframe_mandate": group_by(("timeframe", "mandate")),
        "by_classification_timeframe": group_by(("classification", "timeframe")),
        "by_classification_timeframe_mandate": group_by(("classification", "timeframe", "mandate")),
    }


def _classify_from_metrics(*, record: Dict[str, Any]) -> str:
    drawdown_reduction_threshold_pct = float(record["criteria"]["drawdown_reduction_threshold_pct"])
    net_profit_max_decline_pct = float(record["criteria"]["net_profit_max_decline_pct"])
    drawdown_reduction_pct = float(record["risk"]["drawdown_reduction_pct"])
    net_profit_delta_pct = float(record["risk"]["net_profit_delta_pct"])

    if drawdown_reduction_pct >= drawdown_reduction_threshold_pct and net_profit_delta_pct >= -net_profit_max_decline_pct:
        return "RISK_FILTER_PROTECTIVE"
    if drawdown_reduction_pct < 0 or net_profit_delta_pct < -net_profit_max_decline_pct:
        return "DETRIMENTAL"
    return "NEUTRAL"


def _gate_check_record(record: Dict[str, Any]) -> Dict[str, Any]:
    observed = str(record.get("classification", "UNKNOWN"))
    expected = _classify_from_metrics(record=record)
    ok = observed == expected
    return {
        "status": "PASS" if ok else "FAIL",
        "observed": observed,
        "expected": expected,
        "reason": None if ok else "classification_not_consistent_with_metrics",
    }


def _group_rows(records: List[Dict[str, Any]], keys: Tuple[str, ...]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[tuple(record.get(key) for key in keys)].append(record)

    rows: List[Dict[str, Any]] = []
    for key_tuple, items in sorted(grouped.items(), key=lambda entry: tuple(str(value) for value in entry[0])):
        gate_checks = [_gate_check_record(item) for item in items]
        fail_count = sum(1 for check in gate_checks if check["status"] != "PASS")
        blocked_rate = mean(item["signals"]["blocked_rate"] for item in items)
        execution_rate = mean(item["signals"]["execution_rate"] for item in items)

        row: Dict[str, Any] = {
            "count": len(items),
            "raw_signals_per_day": round(mean(item["signals"]["raw_per_day"] for item in items), 4),
            "executed_signals_per_day": round(mean(item["signals"]["executed_per_day"] for item in items), 4),
            "blocked_rate": round(blocked_rate, 4),
            "blocked_rate_pct": round(blocked_rate * 100.0, 2),
            "execution_rate": round(execution_rate, 4),
            "execution_rate_pct": round(execution_rate * 100.0, 2),
            "drawdown_reduction_pct": round(mean(item["risk"]["drawdown_reduction_pct"] for item in items), 4),
            "net_profit_delta_pct": round(mean(item["risk"]["net_profit_delta_pct"] for item in items), 4),
            "capital_protected": round(sum(item["risk"]["capital_protected"] for item in items), 8),
            "gate": {
                "status": "PASS" if fail_count == 0 else "FAIL",
                "pass_count": len(items) - fail_count,
                "fail_count": fail_count,
            },
        }
        for index, key in enumerate(keys):
            row[key] = key_tuple[index]
        rows.append(row)

    return rows


def _acceptance_gates(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_version: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_version[str(record.get("version", "unknown"))].append(record)

    gates: List[Dict[str, Any]] = []
    for version, meta in VERSION_METADATA.items():
        items = by_version.get(version, [])
        if not items:
            gates.append(
                {
                    "id": f"acceptance:{version}",
                    "version": version,
                    "label": f"{version} - {meta['regime']}",
                    "status": "FAIL",
                    "tone": "fail",
                    "expected_classification": meta["expected_classification"],
                    "observed_classification": "MISSING",
                    "reason": "missing_version_in_series",
                }
            )
            continue

        classifications = sorted({str(item.get("classification", "UNKNOWN")) for item in items})
        if len(classifications) != 1:
            gates.append(
                {
                    "id": f"acceptance:{version}",
                    "version": version,
                    "label": f"{version} - {meta['regime']}",
                    "status": "FAIL",
                    "tone": "fail",
                    "expected_classification": meta["expected_classification"],
                    "observed_classification": "MIXED",
                    "reason": f"mixed_classification:{'|'.join(classifications)}",
                }
            )
            continue

        observed = classifications[0]
        status = "PASS" if observed == meta["expected_classification"] else "FAIL"
        gates.append(
            {
                "id": f"acceptance:{version}",
                "version": version,
                "label": f"{version} - {meta['regime']}",
                "status": status,
                "tone": "pass" if status == "PASS" else "fail",
                "expected_classification": meta["expected_classification"],
                "observed_classification": observed,
                "reason": None if status == "PASS" else "classification_mismatch",
            }
        )

    return gates


def build_views(*, series: List[Dict[str, Any]], aggregates: Dict[str, Any]) -> Dict[str, Any]:
    datasets: Dict[str, str] = {}
    strategies: Dict[str, str | None] = {}
    for record in series:
        datasets[str(record["dataset"])] = str(record["dataset_sha256"])
        strategies[str(record["strategy"])] = record.get("strategy_sha256")

    dataset_rows = [{"dataset": name, "sha256": sha256} for name, sha256 in sorted(datasets.items())]
    strategy_rows = [{"strategy": name, "sha256": sha256} for name, sha256 in sorted(strategies.items())]

    acceptance = _acceptance_gates(series)
    acceptance_ok = all(item["status"] == "PASS" for item in acceptance) if acceptance else False
    acceptance_by_version = {str(item["version"]): item for item in acceptance if "version" in item}

    executive_cards = [
        {"id": "raw_signals_per_day", "label": "Raw signals / day", "value": aggregates["overall"]["raw_signals_per_day"], "unit": "per_day"},
        {"id": "execution_rate_pct", "label": "Execution rate", "value": round(float(aggregates["overall"]["execution_rate"]) * 100.0, 2), "unit": "pct"},
        {"id": "blocked_rate_pct", "label": "Block rate", "value": round(float(aggregates["overall"]["blocked_rate"]) * 100.0, 2), "unit": "pct"},
        {"id": "capital_protected", "label": "Capital protegido", "value": aggregates["overall"]["capital_protected"], "unit": "currency"},
        {"id": "acceptance_gates", "label": "Acceptance gates", "value": "PASS" if acceptance_ok else "FAIL", "tone": "pass" if acceptance_ok else "fail"},
    ]

    dimension_rows = _group_rows(series, ("classification", "timeframe", "mandate"))
    day_rows = _group_rows(series, ("day",))
    regime_rows = _group_rows(series, ("version",))
    for row in regime_rows:
        version = str(row.get("version"))
        row["regime"] = VERSION_METADATA.get(version, {}).get("regime", "Regime desconhecido")
        row["expected_classification"] = VERSION_METADATA.get(version, {}).get("expected_classification", "UNKNOWN")
        row["observed_classification"] = acceptance_by_version.get(version, {}).get("observed_classification", "UNKNOWN")
        row["acceptance_status"] = acceptance_by_version.get(version, {}).get("status", "FAIL")

    return {
        "executive_cards": executive_cards,
        "acceptance_gates": acceptance,
        "tables": {
            "by_dimension": {
                "group_by": ["classification", "timeframe", "mandate"],
                "rows": dimension_rows,
            },
            "by_day": {
                "group_by": ["day"],
                "rows": day_rows,
            },
        },
        "regimes": regime_rows,
        "integrity": {
            "datasets": dataset_rows,
            "strategies": strategy_rows,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Agrega a serie institucional de stress tests do RiskFilter.")
    parser.add_argument(
        "--reports-glob",
        default=DEFAULT_REPORT_GLOB,
        help="Padrao glob para localizar stress_test_report.json gerados pela serie.",
    )
    parser.add_argument(
        "--output",
        default=str(DOCS_OUTPUT),
        help="Arquivo JSON principal de saida para o overview institucional.",
    )
    parser.add_argument(
        "--frontend-output",
        default=str(FRONTEND_OUTPUT),
        help="Snapshot JSON para consumo do frontend institucional.",
    )
    args = parser.parse_args()

    report_paths = sorted(ROOT_DIR.glob(args.reports_glob))
    if not report_paths:
        raise RuntimeError(f"Nenhum report encontrado com o padrao: {args.reports_glob}")

    series = [build_series_record(path) for path in report_paths]
    aggregates = aggregate(series)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "run_id": None,
        "schema_version": SCHEMA_VERSION,
        "integrity": {
            "risk_filter_version": RISK_FILTER_VERSION,
            "runner_sha256": _sha256_file(ROOT_DIR / "run_risk_filter_aggregation.py"),
        },
        "source_reports": [str(path.relative_to(ROOT_DIR)) for path in report_paths],
        "series": series,
        "aggregates": aggregates,
        "views": build_views(series=series, aggregates=aggregates),
    }

    canonical_payload = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    snapshot_checksum = _sha256_text(canonical_payload)
    payload["run_id"] = snapshot_checksum[:16]
    payload["integrity"]["snapshot_checksum"] = snapshot_checksum

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    frontend_path = Path(args.frontend_output)
    frontend_path.parent.mkdir(parents=True, exist_ok=True)
    frontend_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    print(json.dumps(payload, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
