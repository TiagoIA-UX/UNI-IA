"""Testes do ledger DOC (opcional por ambiente)."""

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class DocLedgerTests(unittest.TestCase):
    def test_disabled_writes_nothing(self):
        import core.doc_ledger as dl

        with tempfile.TemporaryDirectory() as td:
            p = str(Path(td) / "l.jsonl")
            with patch.dict(os.environ, {"DOC_LEDGER_ENABLED": "false", "DOC_LEDGER_PATH": p}, clear=False):
                importlib.reload(dl)
                dl.record_broker_execution(
                    provider="mercadobitcoin",
                    payload_sent={"symbol": "BTCBRL", "side": "BUY", "meta": {}},
                    broker_response={"price_brl": 400000.0, "qty": "0.0001"},
                )
            self.assertFalse(Path(p).exists())

    def test_enabled_appends_line_with_hash(self):
        import core.doc_ledger as dl

        with tempfile.TemporaryDirectory() as td:
            p = str(Path(td) / "l.jsonl")
            with patch.dict(os.environ, {"DOC_LEDGER_ENABLED": "true", "DOC_LEDGER_PATH": p}, clear=False):
                importlib.reload(dl)
                dl.record_broker_execution(
                    provider="mercadobitcoin",
                    payload_sent={
                        "symbol": "BTCBRL",
                        "side": "BUY",
                        "qty": "0.0001",
                        "meta": {"chart_timeframe": "5m"},
                    },
                    broker_response={
                        "price_brl": 400000.0,
                        "qty": "0.0001",
                        "broker": "mercadobitcoin",
                    },
                )
            lines = Path(p).read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            row = json.loads(lines[0])
            self.assertEqual(row["tipo"], "EXECUCAO_BROKER")
            self.assertEqual(len(row.get("hash_sha256_linha", "")), 64)


if __name__ == "__main__":
    unittest.main()
