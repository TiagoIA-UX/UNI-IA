"""
StopWatcher — monitor de stop loss / take-profit simulado (MB sem stop nativo na TAPI).

Persiste posições em disco; alerta admin no Telegram em falhas repetidas ou execução falhada.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("stop_watcher")

_RUNTIME_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POSITIONS_FILE = _RUNTIME_ROOT / "runtime_logs" / "open_positions.jsonl"


@dataclass
class StopPosition:
    position_id: str
    asset: str
    direction: str  # "long" | "short"
    entry_price: float
    quantity: float
    stop_loss: float
    stop_gain: float
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    alert_sent_at_pct: Optional[float] = None


class StopWatcher:
    """Monitor em thread daemon; callbacks injetados (preço, execução, alerta Telegram)."""

    CHECK_INTERVAL_SECONDS = float(os.getenv("STOP_WATCHER_INTERVAL_SECONDS", "5"))
    WARNING_THRESHOLD_PCT = float(os.getenv("STOP_WARNING_THRESHOLD_PCT", "0.5"))
    MAX_FAILURES_BEFORE_ALERT = 3

    def __init__(
        self,
        price_fetcher: Callable[[str], float],
        order_executor: Callable[[StopPosition, str], Dict[str, Any]],
        telegram_alerter: Callable[[str], None],
        positions_file: Optional[Path] = None,
    ):
        self.price_fetcher = price_fetcher
        self.order_executor = order_executor
        self.telegram_alerter = telegram_alerter
        self.POSITIONS_FILE = positions_file or DEFAULT_POSITIONS_FILE
        self._positions: Dict[str, StopPosition] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._load_persisted_positions()

    def add_position(self, position: StopPosition) -> None:
        with self._lock:
            self._positions[position.position_id] = position
            self._persist_positions()
        logger.info(
            "[StopWatcher] Posição registrada: %s | %s %s | SL=%s SG=%s",
            position.position_id,
            position.asset,
            position.direction,
            position.stop_loss,
            position.stop_gain,
        )
        try:
            self.telegram_alerter(
                f"📍 <b>Posição registrada no stop watcher</b>\n"
                f"ID: <code>{position.position_id}</code>\n"
                f"Ativo: <b>{position.asset}</b> | Direção: <b>{position.direction.upper()}</b>\n"
                f"Entrada: R$ {position.entry_price:,.2f}\n"
                f"Stop Loss: R$ {position.stop_loss:,.2f}\n"
                f"Stop Gain: R$ {position.stop_gain:,.2f}\n"
                f"Quantidade: {position.quantity:.6f}"
            )
        except Exception as exc:
            logger.warning("telegram_alerter (add): %s", exc)

    def remove_position(self, position_id: str) -> None:
        with self._lock:
            self._positions.pop(position_id, None)
            self._persist_positions()

    def get_positions(self) -> Dict[str, StopPosition]:
        with self._lock:
            return dict(self._positions)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _persist_positions(self) -> None:
        try:
            self.POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with self.POSITIONS_FILE.open("w", encoding="utf-8") as fp:
                for pos in self._positions.values():
                    fp.write(json.dumps(asdict(pos), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("[StopWatcher] Falha ao persistir: %s", exc)

    def _load_persisted_positions(self) -> None:
        if not self.POSITIONS_FILE.exists():
            return
        try:
            with self.POSITIONS_FILE.open("r", encoding="utf-8") as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    pos = StopPosition(**{k: v for k, v in data.items() if k in StopPosition.__dataclass_fields__})
                    self._positions[pos.position_id] = pos
            if self._positions:
                n = len(self._positions)
                logger.warning("[StopWatcher] %s posição(ões) recuperada(s) do disco", n)
                try:
                    self.telegram_alerter(
                        f"⚠️ <b>StopWatcher — Posições recuperadas após reinicialização</b>\n"
                        f"{n} posição(ões) reaberta(s) em monitoramento.\n"
                        f"<i>Confirme SL/SG e exposição.</i>"
                    )
                    for pos in list(self._positions.values()):
                        self.telegram_alerter(
                            f"📂 <b>Posição recuperada</b>\n"
                            f"ID: <code>{pos.position_id}</code>\n"
                            f"Ativo: {pos.asset} | {pos.direction.upper()}\n"
                            f"SL: R$ {pos.stop_loss:,.2f} | SG: R$ {pos.stop_gain:,.2f}"
                        )
                except Exception as exc:
                    logger.warning("telegram_alerter (load): %s", exc)
        except Exception as exc:
            logger.error("[StopWatcher] Falha ao carregar persistência: %s", exc)
            try:
                self.telegram_alerter(
                    f"🔴 <b>StopWatcher — ERRO ao recuperar posições</b>\n"
                    f"<code>{str(exc)[:300]}</code>"
                )
            except Exception:
                pass

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="stop-watcher", daemon=True)
        self._thread.start()
        logger.info("[StopWatcher] Loop iniciado (intervalo %.1fs)", self.CHECK_INTERVAL_SECONDS)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        self._thread = None

    def _run_loop(self) -> None:
        consecutive_failures = 0
        while not self._stop_event.is_set():
            try:
                self._check_all_positions()
                consecutive_failures = 0
            except Exception as exc:
                consecutive_failures += 1
                logger.error("[StopWatcher] Erro no ciclo: %s", exc)
                if consecutive_failures >= self.MAX_FAILURES_BEFORE_ALERT:
                    try:
                        lines = [
                            f"• {p.asset} {p.direction.upper()} | SL: R$ {p.stop_loss:,.2f}"
                            for p in self._positions.values()
                        ]
                        self.telegram_alerter(
                            f"🔴 <b>StopWatcher — FALHA CRÍTICA</b>\n"
                            f"O monitor falhou {consecutive_failures}x seguidas.\n"
                            f"Erro: <code>{str(exc)[:300]}</code>\n\n"
                            f"<b>Posições em risco (sem monitoramento garantido):</b>\n"
                            + ("\n".join(lines) if lines else "(nenhuma registrada)")
                        )
                    except Exception as alert_exc:
                        logger.warning("telegram_alerter (loop): %s", alert_exc)
                    consecutive_failures = 0
            self._stop_event.wait(self.CHECK_INTERVAL_SECONDS)

    def _check_all_positions(self) -> None:
        with self._lock:
            positions = list(self._positions.values())
        for pos in positions:
            try:
                price = self.price_fetcher(pos.asset)
                self._evaluate_stop(pos, float(price))
            except Exception as exc:
                logger.error("[StopWatcher] Erro ao checar %s: %s", pos.position_id, exc)

    def _evaluate_stop(self, pos: StopPosition, current_price: float) -> None:
        triggered = False
        reason = ""

        if pos.direction == "long":
            if current_price <= pos.stop_loss:
                triggered = True
                reason = f"stop_loss_atingido (preço={current_price:.2f} ≤ SL={pos.stop_loss:.2f})"
            elif current_price >= pos.stop_gain:
                triggered = True
                reason = f"stop_gain_atingido (preço={current_price:.2f} ≥ SG={pos.stop_gain:.2f})"
            else:
                span = pos.entry_price - pos.stop_loss
                if span > 1e-9 and pos.entry_price > pos.stop_loss:
                    pct_to_sl = (pos.entry_price - current_price) / span
                    if (
                        pct_to_sl >= self.WARNING_THRESHOLD_PCT
                        and (pos.alert_sent_at_pct is None or abs(pos.alert_sent_at_pct - pct_to_sl) > 0.05)
                    ):
                        pos.alert_sent_at_pct = pct_to_sl
                        with self._lock:
                            if pos.position_id in self._positions:
                                self._positions[pos.position_id] = pos
                                self._persist_positions()
                        try:
                            self.telegram_alerter(
                                f"⚠️ <b>Preço aproximando do Stop Loss</b>\n"
                                f"{pos.asset} LONG | atual R$ {current_price:,.2f} | SL R$ {pos.stop_loss:,.2f}"
                            )
                        except Exception as exc:
                            logger.warning("telegram_alerter (warn): %s", exc)

        elif pos.direction == "short":
            if current_price >= pos.stop_loss:
                triggered = True
                reason = f"stop_loss_atingido (preço={current_price:.2f} ≥ SL={pos.stop_loss:.2f})"
            elif current_price <= pos.stop_gain:
                triggered = True
                reason = f"stop_gain_atingido (preço={current_price:.2f} ≤ SG={pos.stop_gain:.2f})"

        if triggered:
            self._execute_stop(pos, reason, current_price)

    def _execute_stop(self, pos: StopPosition, reason: str, current_price: float) -> None:
        logger.warning("[StopWatcher] Disparando stop: %s | %s", pos.position_id, reason)
        try:
            result = self.order_executor(pos, reason)
            try:
                emoji = "🟢" if "gain" in reason else "🔴"
                self.telegram_alerter(
                    f"{emoji} <b>Stop executado</b>\n"
                    f"ID: <code>{pos.position_id}</code>\n"
                    f"Ativo: {pos.asset} | {pos.direction.upper()}\n"
                    f"Motivo: {reason}\n"
                    f"Preço: R$ {current_price:,.2f}\n"
                    f"Resultado: <code>{str(result)[:200]}</code>"
                )
            except Exception as exc:
                logger.warning("telegram_alerter (ok): %s", exc)
            self.remove_position(pos.position_id)
        except Exception as exc:
            logger.error("[StopWatcher] Falha ao executar stop %s: %s", pos.position_id, exc)
            try:
                self.telegram_alerter(
                    f"🔴 <b>FALHA CRÍTICA: Stop NÃO executado</b>\n"
                    f"ID: <code>{pos.position_id}</code>\n"
                    f"{pos.asset} | {reason}\n"
                    f"Erro: <code>{str(exc)[:300]}</code>\n"
                    f"<b>Intervenção manual necessária.</b>"
                )
            except Exception as alert_exc:
                logger.warning("telegram_alerter (fail): %s", alert_exc)
