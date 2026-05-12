"""
Ledger append-only para rastreio fiscal pré-contábil (DOC) — opcional via ambiente.

- Nunca levanta exceção ao registrador principal (falhas são logadas).
- Não substitui extrato oficial da exchange nem GCAP/DARF — é evidência técnica local.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def _default_ledger_path() -> Path:
    env = os.getenv("DOC_LEDGER_PATH", "").strip()
    if env:
        return Path(env).expanduser()
    if os.name == "nt":
        return Path(r"C:\BoitataDOC\data\doc_ledger.jsonl")
    return Path.home() / "BoitataDOC" / "data" / "doc_ledger.jsonl"


def _enabled() -> bool:
    return os.getenv("DOC_LEDGER_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")


def fiscal_hint_preliminar(chart_tf: Optional[str]) -> str:
    """
    Indício documental só para arquivo — classificação definitiva DAY/SWING
    é por calendário de abertura/fecho (RFB / contador).
    """
    if not chart_tf or not str(chart_tf).strip():
        return "PRELIMINAR_INDEFINIDO_CONFERIR_DATAS_CALENDARIO"
    try:
        from core.chart_timeframes import normalize_chart_timeframe

        n = normalize_chart_timeframe(chart_tf.strip())
    except Exception:
        n = None
    if not n:
        return "PRELIMINAR_INDEFINIDO_TF_BRUTO"
    n = str(n).lower()
    if n in ("1m", "2m", "5m", "15m", "30m"):
        return "CONTEXTO_INTRADIARIO_ALERTA_DAY_TRADE"
    if n == "1h":
        return "CONTEXTO_H1_DOCUMENTAR_FECHO_MESMO_DIA_OU_SWING"
    if n in ("4h", "1d"):
        return "CONTEXTO_MAIOR_PRAZO_FAVORECE_ANALISE_SWING_DOCUMENTAR_DATAS"
    if n in ("1wk", "1mo", "3mo"):
        return "CONTEXTO_MACRO_DOCUMENTAR_SEM_ENTRADA_DIRETA_COMO_SWING_SEM_ABERT_FECHO"
    return "PRELIMINAR_OUTROS_CONFERIR_CONTADOR"


def _estimate_notional_brl(provider: str, broker_resp: Dict[str, Any], payload: Dict[str, Any]) -> Optional[float]:
    try:
        if provider == "mercadobitcoin":
            px = float(broker_resp.get("price_brl") or 0)
            qty = float(broker_resp.get("qty") or payload.get("qty") or 0)
            if px > 0 and qty > 0:
                return round(px * qty, 2)
    except (TypeError, ValueError):
        pass
    return None


def _line_hash(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def record_broker_execution(
    *,
    provider: str,
    payload_sent: Dict[str, Any],
    broker_response: Any,
) -> None:
    if not _enabled():
        return
    if not isinstance(broker_response, dict):
        logger.warning("DOC ledger: broker_response ignorado (nao dict).")
        return

    meta = payload_sent.get("meta") if isinstance(payload_sent.get("meta"), dict) else {}
    chart_tf = meta.get("chart_timeframe") or meta.get("strategy_timeframe")

    event: Dict[str, Any] = {
        "tipo": "EXECUCAO_BROKER",
        "id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "broker_provider": provider,
        "symbol": payload_sent.get("symbol"),
        "side": payload_sent.get("side"),
        "qty": broker_response.get("qty") if provider == "mercadobitcoin" else payload_sent.get("qty"),
        "price_reference_brl": broker_response.get("price_brl") if provider == "mercadobitcoin" else None,
        "volume_financeiro_estimado_brl": _estimate_notional_brl(provider, broker_response, payload_sent),
        "chart_timeframe_ui": meta.get("chart_timeframe"),
        "strategy_timeframe_analise": meta.get("strategy_timeframe"),
        "hint_fiscal_preliminar": fiscal_hint_preliminar(chart_tf),
        "fonte_pipeline": meta.get("source") or meta.get("strategy_tag") or "copy_trade",
        "aviso": "Registo técnico local; conferir Normas RFB vigentes com contabilista antes de declarar.",
    }

    exchange_code = (
        "MERCADO_BITCOIN"
        if provider == "mercadobitcoin"
        else "BYBIT"
        if provider == "bybit"
        else "GENERIC_HTTP"
    )
    event["exchange_codigo_interno"] = exchange_code

    event["hash_sha256_linha"] = _line_hash({k: v for k, v in event.items() if k != "hash_sha256_linha"})

    path = _default_ledger_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, ensure_ascii=False, default=str) + "\n"
        with _lock:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        logger.info("DOC ledger: registo %s em %s", event["id"], path)
    except OSError as e:
        logger.warning("DOC ledger: falha ao escrever em %s: %s", path, e)
