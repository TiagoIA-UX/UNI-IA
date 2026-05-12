import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.telegram_bot import UniIATelegramBot
from core.schemas import OpportunityAlert, StrategyDecision


class TelegramBotFormatTests(unittest.TestCase):
    def test_format_message_escapes_html_in_dynamic_fields(self):
        bot = UniIATelegramBot()
        strat = StrategyDecision(
            mode="FAST_SCALP",
            direction="long",
            timeframe="5m",
            confidence=0.7,
            operational_status="ok",
            reasons=["use <script>x</script>", "a & b"],
            execution_hint="price < 100 && > 50",
        )
        alert = OpportunityAlert(
            asset="BTCBRL",
            score=80.0,
            classification="OPORTUNIDADE",
            explanation="Leitura com <tag> e caracteres & especiais",
            sources=[],
            strategy=strat,
        )
        msg = bot._format_message(alert, is_premium=True)
        self.assertNotIn("<script>", msg)
        self.assertIn("&lt;script&gt;", msg)
        self.assertIn("&amp;", msg)
        self.assertIn("<b>", msg)


if __name__ == "__main__":
    unittest.main()
