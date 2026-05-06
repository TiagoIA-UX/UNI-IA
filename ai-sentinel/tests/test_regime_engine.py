import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from core.regime_engine import RegimeEngine
from core.schemas import AgentSignal


class RegimeEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RegimeEngine()

    def test_classifies_event_driven_when_surprise_is_high(self):
        context = self.engine.classify(
            asset="BTCUSDT",
            macro_signal=AgentSignal(agent_name="MacroAgent", asset="BTCUSDT", signal_type="RISK-ON", confidence=80.0, summary="macro"),
            atlas_signal=AgentSignal(agent_name="ATLAS", asset="BTCUSDT", signal_type="STRONG BUY", confidence=85.0, summary="atlas"),
            orion_signal=AgentSignal(agent_name="ORION", asset="BTCUSDT", signal_type="BULLISH", confidence=82.0, summary="orion"),
            news_signal=AgentSignal(agent_name="NewsAgent", asset="BTCUSDT", signal_type="BULLISH", confidence=78.0, summary="news"),
            macro_features={"recent_volume": 1000000, "daily_variation_pct": 2.5},
            atlas_features={"atr_regime": "high", "structure_trend": "bullish"},
            orion_features={"regime": "RISK-ON", "surprise_ratio_pct": 80.0, "high_surprise_count": 3, "sentiment_score": 70.0},
            news_features={"headline_count": 8},
        )

        self.assertEqual(context.regime_id, "event_driven")
        self.assertEqual(context.regime_version, RegimeEngine.VERSION)
        self.assertGreaterEqual(context.regime_confidence, 80.0)

    def test_classifies_trend_risk_on_when_structure_and_macro_align(self):
        context = self.engine.classify(
            asset="BTCUSDT",
            macro_signal=AgentSignal(agent_name="MacroAgent", asset="BTCUSDT", signal_type="RISK-ON", confidence=75.0, summary="macro"),
            atlas_signal=AgentSignal(agent_name="ATLAS", asset="BTCUSDT", signal_type="STRONG BUY", confidence=88.0, summary="atlas"),
            orion_signal=AgentSignal(agent_name="ORION", asset="BTCUSDT", signal_type="BULLISH", confidence=74.0, summary="orion"),
            news_signal=AgentSignal(agent_name="NewsAgent", asset="BTCUSDT", signal_type="BULLISH", confidence=72.0, summary="news"),
            macro_features={"recent_volume": 500000, "daily_variation_pct": 1.2},
            atlas_features={"atr_regime": "normal", "structure_trend": "bullish"},
            orion_features={"regime": "RISK-ON", "surprise_ratio_pct": 10.0, "high_surprise_count": 0, "sentiment_score": 55.0},
            news_features={"headline_count": 4},
        )

        self.assertEqual(context.regime_id, "trend_risk_on")
        self.assertEqual(context.market_structure, "bullish")
        self.assertEqual(context.macro_regime, "RISK-ON")


if __name__ == "__main__":
    unittest.main()