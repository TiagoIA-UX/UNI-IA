"""Contrato LlmProvenance / AgentSignal (camada schema)."""

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.schemas import AgentSignal, LlmProvenance


class LlmProvenanceSchemaTests(unittest.TestCase):
    def test_agent_signal_serializes_provenance(self):
        sig = AgentSignal(
            agent_name="ORION",
            asset="BTC-BRL",
            signal_type="NEUTRAL",
            confidence=40.0,
            summary="sem rss",
            llm_provenance=LlmProvenance(provider="none", model=None, status="llm_skipped", detail="no_rss"),
        )
        d = sig.model_dump()
        self.assertEqual(d["llm_provenance"]["status"], "llm_skipped")
        self.assertEqual(d["llm_provenance"]["provider"], "none")


if __name__ == "__main__":
    unittest.main()
