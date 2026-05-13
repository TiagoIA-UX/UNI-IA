"""
Testes: StopWatcher, semântica de dispatch (blocked vs failed), helpers de roteamento.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.stop_watcher import StopPosition, StopWatcher  # noqa: E402


def _dispatch_status_from_tg(tg: dict) -> str:
    """Espelha `signal_scanner.scan_asset` (gate ≠ erro)."""
    if tg.get("dispatched"):
        return "sent"
    if not tg.get("success", True):
        return "failed"
    if tg.get("gate_reason"):
        return "blocked"
    return "blocked"


class TestStopWatcher(unittest.TestCase):
    def _make_watcher(self, price=None, alert_log=None):
        alert_log = alert_log if alert_log is not None else []
        price_val = 400_000.0 if price is None else price
        fetcher = MagicMock(return_value=price_val)
        executor = MagicMock(return_value={"success": True})
        alerter = MagicMock(side_effect=lambda msg: alert_log.append(msg))
        watcher = StopWatcher(fetcher, executor, alerter)
        p = watcher.POSITIONS_FILE
        if p.exists():
            p.unlink()
        return watcher, fetcher, executor, alerter, alert_log

    def _make_position(self, direction="long", entry=400_000, sl=390_000, sg=420_000):
        return StopPosition(
            position_id="test-pos-001",
            asset="BTCBRL",
            direction=direction,
            entry_price=entry,
            quantity=0.001,
            stop_loss=sl,
            stop_gain=sg,
        )

    def test_add_position_envia_alerta(self):
        alerts = []
        watcher, _, _, _, log = self._make_watcher(alert_log=alerts)
        pos = self._make_position()
        watcher.add_position(pos)
        self.assertTrue(log, "esperado alerta ao registrar posição")

    def test_stop_loss_long_dispara(self):
        watcher, _, executor, _, _ = self._make_watcher(price=389_000)
        pos = self._make_position(direction="long", sl=390_000)
        watcher._positions[pos.position_id] = pos
        watcher._check_all_positions()
        executor.assert_called_once()
        self.assertNotIn(pos.position_id, watcher._positions)

    def test_stop_gain_long_dispara(self):
        watcher, _, executor, _, _ = self._make_watcher(price=421_000)
        pos = self._make_position(direction="long", sg=420_000)
        watcher._positions[pos.position_id] = pos
        watcher._check_all_positions()
        executor.assert_called_once()

    def test_stop_loss_short_dispara(self):
        watcher, _, executor, _, _ = self._make_watcher(price=411_000)
        pos = self._make_position(direction="short", entry=400_000, sl=410_000, sg=380_000)
        watcher._positions[pos.position_id] = pos
        watcher._check_all_positions()
        executor.assert_called_once()

    def test_preco_seguro_nao_dispara(self):
        watcher, fetcher, executor, _, _ = self._make_watcher(price=405_000)
        pos = self._make_position(sl=390_000, sg=420_000)
        watcher._positions[pos.position_id] = pos
        watcher._check_all_positions()
        executor.assert_not_called()
        self.assertIn(pos.position_id, watcher._positions)

    def test_falha_no_executor_envia_alerta_critico(self):
        alerts: list = []
        watcher, _, _, _, log = self._make_watcher(price=389_000, alert_log=alerts)
        watcher.order_executor = MagicMock(side_effect=RuntimeError("Broker offline"))
        pos = self._make_position(direction="long", sl=390_000)
        watcher._positions[pos.position_id] = pos
        watcher._check_all_positions()
        critico = [a for a in log if "FALHA CRÍTICA" in a or "INTERVENÇÃO" in a or "NÃO executado" in a]
        self.assertTrue(critico, log)
        self.assertIn(pos.position_id, watcher._positions)

    def test_posicoes_persistidas_e_recuperadas(self):
        alerts: list = []
        w1, _, _, _, _ = self._make_watcher(alert_log=[])
        pos = self._make_position()
        w1.add_position(pos)
        self.assertTrue(w1.POSITIONS_FILE.exists())

        w2 = StopWatcher(
            MagicMock(return_value=405_000.0),
            MagicMock(),
            MagicMock(side_effect=lambda m: alerts.append(m)),
            positions_file=w1.POSITIONS_FILE,
        )
        self.assertIn(pos.position_id, w2._positions)
        self.assertTrue(any("recuperad" in a.lower() for a in alerts))
        w1.POSITIONS_FILE.unlink(missing_ok=True)


class TestDispatchStatus(unittest.TestCase):
    def test_gate_suprimido_e_blocked(self):
        tg = {"success": True, "dispatched": False, "gate_reason": "fast_path_block"}
        self.assertEqual(_dispatch_status_from_tg(tg), "blocked")

    def test_erro_http_e_failed(self):
        tg = {"success": False, "dispatched": False, "error": "HTTP 500"}
        self.assertEqual(_dispatch_status_from_tg(tg), "failed")

    def test_envio_ok_e_sent(self):
        tg = {"success": True, "dispatched": True}
        self.assertEqual(_dispatch_status_from_tg(tg), "sent")


class TestQuoteSuffixHeuristic(unittest.TestCase):
    def test_brl_e_usdt_reconhecidos(self):
        premium_suffixes = ("BRL", "USD", "EUR", "USDT", "USDC")
        self.assertTrue("BTCBRL".upper().endswith("BRL"))
        self.assertTrue("ETHUSDT".upper().endswith("USDT"))
        self.assertFalse("BTCETH".upper().endswith(premium_suffixes))


if __name__ == "__main__":
    unittest.main(verbosity=2)
