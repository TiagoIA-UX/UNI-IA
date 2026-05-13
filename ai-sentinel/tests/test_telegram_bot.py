import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.telegram_bot import UniIATelegramBot
from core.schemas import OpportunityAlert, StrategyDecision, SentinelGovernanceDecision


def _gov(*, approved: bool) -> SentinelGovernanceDecision:
    return SentinelGovernanceDecision(
        signal_id="test-sid",
        regime_id="reg",
        regime_version="v1",
        sentinel_decision="allow" if approved else "block",
        sentinel_confidence=88.0,
        block_reason_code="none" if approved else "test_block",
        expected_confidence_delta=0.0,
        approved=approved,
        reason_codes=[] if approved else ["test_reason"],
        risk_flags=[],
    )


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


class TelegramDispatchGateTests(unittest.TestCase):
    """Garante que sinais fracos, bloqueados ou incompletos nao vao a canais publicos."""

    def _base_alert(self) -> OpportunityAlert:
        strat = StrategyDecision(
            mode="swing",
            direction="long",
            timeframe="1h",
            confidence=80.0,
            operational_status="ok",
            reasons=["test"],
        )
        return OpportunityAlert(
            asset="BTCBRL",
            score=80.0,
            classification="OPORTUNIDADE",
            explanation="Teste",
            sources=["test"],
            strategy=strat,
            governance=_gov(approved=True),
            integrity_score=95.0,
            fast_path_decision="long",
        )

    def test_skips_when_sentinel_not_approved(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.governance = _gov(approved=False)
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertFalse(ok)
        self.assertEqual(reason, "sentinel_nao_aprovou")

    def test_skips_when_governance_missing_and_required(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.governance = None
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertFalse(ok)
        self.assertEqual(reason, "governance_ausente")

    def test_skips_when_fast_path_block(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.fast_path_decision = "block"
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertFalse(ok)
        self.assertEqual(reason, "fast_path_block")

    def test_skips_when_classification_not_allowlisted(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.classification = "RISCO"
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertFalse(ok)
        self.assertIn("fora_da_lista", reason)

    def test_skips_when_direction_flat(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.strategy = StrategyDecision(
            mode="swing",
            direction="flat",
            timeframe="1h",
            confidence=50.0,
            operational_status="ok",
            reasons=["flat"],
        )
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertFalse(ok)
        self.assertEqual(reason, "direcao_flat")

    def test_skips_when_strategy_missing(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.strategy = None
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertFalse(ok)
        self.assertEqual(reason, "estrategia_ausente")

    def test_skips_when_integrity_below_minimum(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.integrity_score = 40.0
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertFalse(ok)
        self.assertEqual(reason, "integridade_abaixo_minimo")

    def test_accepts_actionable_opportunity_when_clean(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        ok, reason = bot._should_dispatch_public_alert(alert)
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")

    def test_dispatch_alert_does_not_call_http_when_gated(self):
        bot = UniIATelegramBot()
        alert = self._base_alert()
        alert.governance = _gov(approved=False)
        with patch.object(bot, "_validate_config"):
            with patch.object(bot, "_post_message") as post:
                sent = bot.dispatch_alert(alert)
        post.assert_not_called()
        self.assertFalse(sent)


if __name__ == "__main__":
    unittest.main()
