import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.chart_timeframes import normalize_chart_timeframe, public_timeframes_catalog


class ChartTimeframesCatalogTests(unittest.TestCase):
    def test_catalog_includes_strategy_family(self):
        items = public_timeframes_catalog()
        self.assertGreaterEqual(len(items), 10)
        canon = {x["canonical"]: x for x in items}
        self.assertEqual(canon["1m"]["strategy_family"], "intraday_swings")
        self.assertEqual(canon["5m"]["strategy_family"], "intraday_swings")
        self.assertEqual(canon["15m"]["strategy_family"], "intraday_swings")
        self.assertEqual(canon["1d"]["strategy_family"], "position_gap_session")
        self.assertIn("strategy_family_note", canon["1d"])
        self.assertIn("gap_filter", canon["1d"]["strategy_family_note"])

    def test_normalize_aliases(self):
        self.assertEqual(normalize_chart_timeframe("M15"), "15m")
        self.assertEqual(normalize_chart_timeframe("1d"), "1d")


if __name__ == "__main__":
    unittest.main()
