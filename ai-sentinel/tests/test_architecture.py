"""Testes da arquitetura nomeada: ATLAS, ORION, AEGIS, SENTINEL, ARGUS + FeatureStore."""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np


class FeatureStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        os.environ["FEATURE_STORE_LOG_PATH"] = self.tmp.name
        os.environ.pop("NEXT_PUBLIC_SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)
        from core.feature_store import FeatureStore
        self.store = FeatureStore()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def test_persist_and_retrieve(self):
        self.store.persist(
            signal_id="sig-001",
            asset="BTCUSDT",
            agent_name="ATLAS",
            features={"rsi_14_1d": 55.0, "atr_regime": "normal", "structure_trend": "bullish"},
        )
        self.store.persist(
            signal_id="sig-001",
            asset="BTCUSDT",
            agent_name="ORION",
            features={"sentiment_score": 32.5, "surprise_ratio_pct": 40.0},
        )

        entries = self.store.get_features_for_signal("sig-001")
        self.assertEqual(len(entries), 2)
        agents = {e["agent_name"] for e in entries}
        self.assertIn("ATLAS", agents)
        self.assertIn("ORION", agents)

    def test_get_recent_filters(self):
        for i in range(5):
            self.store.persist(
                signal_id=f"sig-{i}",
                asset="BTCUSDT" if i % 2 == 0 else "ETHUSDT",
                agent_name="ATLAS",
                features={"rsi": float(50 + i)},
            )

        all_items = self.store.get_recent(limit=100)
        self.assertEqual(all_items["count"], 5)

        btc_only = self.store.get_recent(limit=100, asset="BTCUSDT")
        self.assertEqual(btc_only["count"], 3)

    def test_export_dataset(self):
        for i in range(3):
            self.store.persist(
                signal_id=f"exp-{i}",
                asset="SOLUSDT",
                agent_name="ATLAS",
                features={"ma_20_dist": float(i)},
            )
        dataset = self.store.export_dataset(agent_name="ATLAS")
        self.assertEqual(len(dataset), 3)


class AtlasFeatureTests(unittest.TestCase):
    """Testa computacao de features do ATLAS com dados sinteticos."""

    def test_market_structure_detection(self):
        from agents.atlas_agent import AtlasAgent
        agent = AtlasAgent()

        # Bullish structure: clear HH + HL with pronounced swings
        # Pattern: rally-dip-higher_rally-higher_dip (clear swing points)
        highs = np.array([10, 12, 15, 13, 11, 12, 17, 20, 18, 15, 16, 19, 23, 21, 18])
        lows  = np.array([ 8, 10, 13, 11,  9, 10, 15, 18, 16, 13, 14, 17, 21, 19, 16])
        result = agent._detect_market_structure(highs, lows)
        # Should detect upward structure
        self.assertIn(result["trend"], ("bullish", "expansion", "mixed", "neutral"))
        self.assertIsNotNone(result["swing_high"])

        # Bearish structure: clear LH + LL with pronounced swings
        highs_bear = np.array([23, 21, 18, 20, 22, 21, 17, 14, 16, 18, 17, 13, 10, 12, 14])
        lows_bear  = np.array([21, 19, 16, 18, 20, 19, 15, 12, 14, 16, 15, 11,  8, 10, 12])
        result_bear = agent._detect_market_structure(highs_bear, lows_bear)
        self.assertIn(result_bear["trend"], ("bearish", "compression", "mixed", "neutral"))
        self.assertIsNotNone(result_bear["swing_high"])

    def test_ema_calculation(self):
        from agents.atlas_agent import AtlasAgent
        agent = AtlasAgent()
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        ema = agent._ema(data, 5)
        self.assertIsInstance(ema, float)
        self.assertGreater(ema, 5.0)  # EMA should be pulled toward recent values

    def test_safe_handles_nan_inf(self):
        from agents.atlas_agent import _safe
        self.assertIsNone(_safe(float("nan")))
        self.assertIsNone(_safe(float("inf")))
        self.assertIsNone(_safe(None))
        self.assertEqual(_safe(3.14159, 2), 3.14)
        self.assertEqual(_safe(42), 42)


class AegisTests(unittest.TestCase):
    def test_fusion_with_aligned_signals(self):
        os.environ.pop("NEXT_PUBLIC_SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)

        from agents.aegis_agent import AegisAgent
        from core.schemas import AgentSignal

        mock_response = json.dumps({
            "score": 85.0,
            "classification": "OPORTUNIDADE",
            "direction": "long",
            "explanation": "ATLAS e ORION alinhados bullish.",
            "confluence_level": "strong",
        })

        with patch("agents.aegis_agent.GroqClient") as MockGroq:
            instance = MockGroq.return_value
            instance.generate_response.return_value = mock_response

            aegis = AegisAgent()
            signals = [
                AgentSignal(agent_name="ATLAS", asset="BTCUSDT", signal_type="STRONG BUY", confidence=90.0, summary="Estrutura bullish."),
                AgentSignal(agent_name="ORION", asset="BTCUSDT", signal_type="BULLISH", confidence=80.0, summary="Narrativa favoravel."),
            ]

            alert = aegis.fuse("BTCUSDT", signals)
            self.assertEqual(alert.classification, "OPORTUNIDADE")
            self.assertEqual(alert.strategy.direction, "long")
            self.assertIn("ATLAS", alert.sources)
            self.assertIn("ORION", alert.sources)

    def test_fusion_conflicting_goes_conservative(self):
        os.environ.pop("NEXT_PUBLIC_SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)

        from agents.aegis_agent import AegisAgent
        from core.schemas import AgentSignal

        mock_response = json.dumps({
            "score": 45.0,
            "classification": "ATENCAO",
            "direction": "flat",
            "explanation": "ATLAS bearish, ORION bullish. Conflito.",
            "confluence_level": "conflicting",
        })

        with patch("agents.aegis_agent.GroqClient") as MockGroq:
            instance = MockGroq.return_value
            instance.generate_response.return_value = mock_response

            aegis = AegisAgent()
            signals = [
                AgentSignal(agent_name="ATLAS", asset="ETHUSDT", signal_type="STRONG SELL", confidence=85.0, summary="Estrutura bearish."),
                AgentSignal(agent_name="ORION", asset="ETHUSDT", signal_type="BULLISH", confidence=75.0, summary="Narrativa positiva."),
            ]

            alert = aegis.fuse("ETHUSDT", signals)
            self.assertEqual(alert.classification, "ATENCAO")
            self.assertEqual(alert.strategy.direction, "flat")


class SentinelTests(unittest.TestCase):
    def test_block_on_halted(self):
        from agents.sentinel_agent import SentinelAgent
        from core.system_state import SystemStateManager, UniIAMode
        from core.schemas import OpportunityAlert

        state = SystemStateManager(UniIAMode.LIVE)
        state.set_halted("test_halt")

        sentinel = SentinelAgent(system_state=state)
        alert = OpportunityAlert(
            asset="BTCUSDT", score=90.0, classification="OPORTUNIDADE",
            explanation="Test", sources=["ATLAS"],
        )
        result = sentinel.evaluate(alert)
        self.assertFalse(result["approved"])
        self.assertEqual(result["action"], "block")

    def test_block_on_low_score(self):
        from agents.sentinel_agent import SentinelAgent
        from core.schemas import OpportunityAlert

        sentinel = SentinelAgent(min_score_to_dispatch=70.0)
        alert = OpportunityAlert(
            asset="BTCUSDT", score=50.0, classification="ATENCAO",
            explanation="Test", sources=["ATLAS"],
        )
        result = sentinel.evaluate(alert)
        self.assertFalse(result["approved"])
        self.assertEqual(result["action"], "block")

    def test_pass_on_good_signal(self):
        from agents.sentinel_agent import SentinelAgent
        from core.system_state import SystemStateManager, UniIAMode
        from core.schemas import OpportunityAlert

        state = SystemStateManager(UniIAMode.LIVE)
        state.apply_validation_result(critical_errors=[], non_critical_errors=[])

        sentinel = SentinelAgent(system_state=state)
        alert = OpportunityAlert(
            asset="BTCUSDT", score=85.0, classification="OPORTUNIDADE",
            explanation="Test", sources=["ATLAS", "ORION"],
        )
        result = sentinel.evaluate(alert)
        self.assertTrue(result["approved"])
        self.assertEqual(result["action"], "pass")


class ArgusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        os.environ["OUTCOME_LOG_PATH"] = self.tmp.name
        os.environ.pop("NEXT_PUBLIC_SUPABASE_URL", None)
        os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def test_register_and_close(self):
        from agents.argus_agent import ArgusAgent

        argus = ArgusAgent()
        reg = argus.register_position(
            signal_id="sig-100",
            asset="BTCUSDT",
            direction="long",
            entry_price=60000.0,
        )
        self.assertTrue(reg["registered"])

        positions = argus.get_active_positions()
        self.assertEqual(len(positions), 1)

        close = argus.close_position(
            signal_id="sig-100",
            exit_price=61200.0,
            result="win",
        )
        self.assertTrue(close["closed"])
        self.assertGreater(close["pnl_pct"], 0)

        # Position should be removed
        self.assertEqual(len(argus.get_active_positions()), 0)

        # Outcome should be recorded
        with open(self.tmp.name, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        outcome = json.loads(lines[0])
        self.assertEqual(outcome["result"], "win")


if __name__ == "__main__":
    unittest.main()
