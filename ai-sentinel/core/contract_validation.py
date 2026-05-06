import unicodedata
from typing import Any, Iterable, List


VALID_ALERT_CLASSIFICATIONS = {"OPORTUNIDADE", "ATENCAO", "RISCO"}
VALID_DIRECTIONS = {"long", "short", "flat"}
VALID_CONFLUENCE_LEVELS = {"strong", "moderate", "weak", "conflicting"}
VALID_SENTINEL_DECISIONS = {"allow", "block", "downgrade"}


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise RuntimeError(f"{field_name} deve ser string nao vazia.")
    normalized = value.strip()
    if not normalized:
        raise RuntimeError(f"{field_name} deve ser string nao vazia.")
    return normalized


def require_percentage(value: Any, field_name: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{field_name} deve ser numerico.") from exc

    if numeric < 0 or numeric > 100:
        raise RuntimeError(f"{field_name} deve ficar entre 0 e 100.")
    return numeric


def require_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{field_name} deve ser numerico.") from exc


def normalize_classification(value: Any, field_name: str = "classification") -> str:
    normalized = _strip_accents(require_non_empty_string(value, field_name)).upper()
    if normalized not in VALID_ALERT_CLASSIFICATIONS:
        raise RuntimeError(
            f"{field_name} invalido: {normalized}. Esperado: {sorted(VALID_ALERT_CLASSIFICATIONS)}."
        )
    return normalized


def normalize_direction(value: Any, field_name: str = "direction") -> str:
    normalized = require_non_empty_string(value, field_name).strip().lower()
    if normalized not in VALID_DIRECTIONS:
        raise RuntimeError(f"{field_name} invalido: {normalized}. Esperado: {sorted(VALID_DIRECTIONS)}.")
    return normalized


def normalize_sentinel_decision(value: Any, field_name: str = "sentinel_decision") -> str:
    normalized = require_non_empty_string(value, field_name).strip().lower()
    if normalized not in VALID_SENTINEL_DECISIONS:
        raise RuntimeError(
            f"{field_name} invalido: {normalized}. Esperado: {sorted(VALID_SENTINEL_DECISIONS)}."
        )
    return normalized


def normalize_confluence_level(value: Any, field_name: str = "confluence_level") -> str:
    normalized = require_non_empty_string(value, field_name).strip().lower()
    if normalized not in VALID_CONFLUENCE_LEVELS:
        raise RuntimeError(
            f"{field_name} invalido: {normalized}. Esperado: {sorted(VALID_CONFLUENCE_LEVELS)}."
        )
    return normalized


def validate_string_list(items: Any, field_name: str) -> List[str]:
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"{field_name} deve ser uma lista nao vazia.")

    validated: List[str] = []
    seen = set()
    for item in items:
        value = require_non_empty_string(item, field_name)
        if value not in seen:
            validated.append(value)
            seen.add(value)

    if not validated:
        raise RuntimeError(f"{field_name} deve conter ao menos um valor valido.")
    return validated


def validate_optional_string_list(items: Any, field_name: str) -> List[str]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise RuntimeError(f"{field_name} deve ser uma lista.")

    validated: List[str] = []
    seen = set()
    for item in items:
        value = require_non_empty_string(item, field_name)
        if value not in seen:
            validated.append(value)
            seen.add(value)
    return validated


def validate_required_keys(data: Any, required_keys: Iterable[str], context_name: str):
    if not isinstance(data, dict):
        raise RuntimeError(f"{context_name} deve ser um objeto JSON.")

    missing = [key for key in required_keys if data.get(key) in (None, "")]
    if missing:
        raise RuntimeError(f"{context_name} incompleto. Campos obrigatorios ausentes: {', '.join(missing)}")


def validate_agent_signal(signal: Any, *, expected_asset: str | None = None):
    agent_name = require_non_empty_string(getattr(signal, "agent_name", None), "agent_name")
    asset = require_non_empty_string(getattr(signal, "asset", None), "asset").upper()
    if expected_asset and asset != expected_asset.upper().strip():
        raise RuntimeError(f"{agent_name} retornou asset divergente: {asset} != {expected_asset}.")
    signal_type = require_non_empty_string(getattr(signal, "signal_type", None), "signal_type")
    confidence = require_percentage(getattr(signal, "confidence", None), "confidence")
    summary = require_non_empty_string(getattr(signal, "summary", None), "summary")

    signal.agent_name = agent_name
    signal.asset = asset
    signal.signal_type = signal_type
    signal.confidence = confidence
    signal.summary = summary
    return signal


def validate_opportunity_alert(alert: Any, *, expected_asset: str | None = None):
    asset = require_non_empty_string(getattr(alert, "asset", None), "asset").upper()
    if expected_asset and asset != expected_asset.upper().strip():
        raise RuntimeError(f"alert.asset divergente: {asset} != {expected_asset}.")

    score = require_percentage(getattr(alert, "score", None), "score")
    classification = normalize_classification(getattr(alert, "classification", None))
    explanation = require_non_empty_string(getattr(alert, "explanation", None), "explanation")
    sources = validate_string_list(getattr(alert, "sources", None), "sources")

    strategy = getattr(alert, "strategy", None)
    if strategy is not None:
        strategy.mode = require_non_empty_string(getattr(strategy, "mode", None), "strategy.mode")
        strategy.direction = normalize_direction(getattr(strategy, "direction", None), "strategy.direction")
        strategy.timeframe = require_non_empty_string(getattr(strategy, "timeframe", None), "strategy.timeframe")
        strategy.confidence = require_percentage(getattr(strategy, "confidence", None), "strategy.confidence")
        strategy.operational_status = require_non_empty_string(
            getattr(strategy, "operational_status", None),
            "strategy.operational_status",
        )
        strategy.reasons = validate_string_list(getattr(strategy, "reasons", None), "strategy.reasons")
        execution_hint = getattr(strategy, "execution_hint", None)
        if execution_hint is not None:
            strategy.execution_hint = require_non_empty_string(execution_hint, "strategy.execution_hint")
        regime_id = getattr(strategy, "regime_id", None)
        if regime_id is not None:
            strategy.regime_id = require_non_empty_string(regime_id, "strategy.regime_id")
        regime_label = getattr(strategy, "regime_label", None)
        if regime_label is not None:
            strategy.regime_label = require_non_empty_string(regime_label, "strategy.regime_label")
        regime_version = getattr(strategy, "regime_version", None)
        if regime_version is not None:
            strategy.regime_version = require_non_empty_string(regime_version, "strategy.regime_version")
        regime_confidence = getattr(strategy, "regime_confidence", None)
        if regime_confidence is not None:
            strategy.regime_confidence = require_percentage(regime_confidence, "strategy.regime_confidence")

    governance = getattr(alert, "governance", None)
    if governance is not None:
        governance.signal_id = require_non_empty_string(getattr(governance, "signal_id", None), "governance.signal_id")
        governance.regime_id = require_non_empty_string(getattr(governance, "regime_id", None), "governance.regime_id")
        governance.regime_version = require_non_empty_string(
            getattr(governance, "regime_version", None),
            "governance.regime_version",
        )
        governance.sentinel_decision = normalize_sentinel_decision(
            getattr(governance, "sentinel_decision", None),
            "governance.sentinel_decision",
        )
        governance.sentinel_confidence = require_percentage(
            getattr(governance, "sentinel_confidence", None),
            "governance.sentinel_confidence",
        )
        governance.block_reason_code = require_non_empty_string(
            getattr(governance, "block_reason_code", None),
            "governance.block_reason_code",
        )
        governance.expected_confidence_delta = require_float(
            getattr(governance, "expected_confidence_delta", None),
            "governance.expected_confidence_delta",
        )
        if not isinstance(getattr(governance, "approved", None), bool):
            raise RuntimeError("governance.approved deve ser booleano.")
        governance.reason_codes = validate_optional_string_list(
            getattr(governance, "reason_codes", None),
            "governance.reason_codes",
        )
        governance.risk_flags = validate_optional_string_list(
            getattr(governance, "risk_flags", None),
            "governance.risk_flags",
        )

    alert.asset = asset
    alert.score = score
    alert.classification = classification
    alert.explanation = explanation
    alert.sources = sources
    return alert