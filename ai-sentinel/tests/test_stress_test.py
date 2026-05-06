import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from run_stress_test import classify_comparison


class StressTestClassificationTests(unittest.TestCase):
    def test_classifies_protective_when_drawdown_drops_and_profit_is_preserved(self):
        result = classify_comparison(drawdown_reduction_pct=25.0, net_profit_delta_pct=-8.0)
        self.assertEqual(result, "RISK_FILTER_PROTECTIVE")

    def test_classifies_detrimental_when_profit_damage_exceeds_limit(self):
        result = classify_comparison(drawdown_reduction_pct=30.0, net_profit_delta_pct=-25.0)
        self.assertEqual(result, "DETRIMENTAL")

    def test_classifies_neutral_when_improvement_is_insufficient(self):
        result = classify_comparison(drawdown_reduction_pct=10.0, net_profit_delta_pct=-2.0)
        self.assertEqual(result, "NEUTRAL")


if __name__ == "__main__":
    unittest.main()
