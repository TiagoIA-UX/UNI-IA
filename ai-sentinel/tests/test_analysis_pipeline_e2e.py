"""Teste e2e do pipeline de analise com dependencias externas isoladas (yfinance, RSS, Groq)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from llm.groq_client import GroqClient


def _rss_response():
    xml = (
        b'<?xml version="1.0"?><rss version="2.0"><channel>'
        b"<item><title>Test headline e2e</title><pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate></item>"
        b"</channel></rss>"
    )
    r = MagicMock()
    r.content = xml
    r.raise_for_status = MagicMock()
    return r


def _fake_requests_get(url, timeout=10, **kwargs):
    if "news.google" in str(url):
        return _rss_response()
    r = MagicMock()
    r.content = b""
    r.raise_for_status.side_effect = RuntimeError("unexpected url in e2e")
    return r


class _FakeTicker:
    """Ticker minimo para Macro, Atlas, Trends (history / info)."""

    fast_info = SimpleNamespace(last_price=100.0, previous_close=99.0)

    @property
    def info(self):
        return {"currentPrice": 100.0, "previousClose": 99.0, "volume": 1e6}

    def history(self, *args, **kwargs):
        n = 90
        return pd.DataFrame(
            {
                "Open": [100.0] * n,
                "High": [101.0] * n,
                "Low": [99.0] * n,
                "Close": [100.0] * n,
                "Volume": [1e6] * n,
            }
        )


def _groq_complete_e2e(system_prompt: str, user_prompt: str):
    sp = system_prompt
    if "Voce e o AEGIS" in sp or "AEGIS" in sp[:120]:
        payload = {
            "score": 70.0,
            "classification": "ATENCAO",
            "direction": "long",
            "explanation": "e2e fusion",
            "confluence_level": "moderate",
        }
        return SimpleNamespace(text=json.dumps(payload), model="llama-e2e", provider="groq")
    if "Você é o MacroAgent" in sp:
        return SimpleNamespace(
            text='{"signal_type": "NEUTRAL", "confidence": 50, "summary": "macro e2e"}',
            model="llama-e2e",
            provider="groq",
        )
    if "Você é o NewsAgent" in sp:
        return SimpleNamespace(
            text='{"signal_type": "NEUTRAL", "confidence": 50, "summary": "news e2e"}',
            model="llama-e2e",
            provider="groq",
        )
    if "UMA noticia de cada vez" in sp:
        return SimpleNamespace(
            text=(
                '{"polarity": "NEUTRAL", "impact_score": 10, "surprise_level": "NONE", '
                '"impact_horizon": "short_term", "category": "other", "summary": "c"}'
            ),
            model="llama-e2e",
            provider="groq",
        )
    if "VETOR NUMERICO consolidado" in sp:
        return SimpleNamespace(
            text=(
                '{"signal_type": "NEUTRAL", "confidence": 50, "regime": "TRANSITIONAL", '
                '"regime_shift_probability": 0, "summary": "orion e2e"}'
            ),
            model="llama-e2e",
            provider="groq",
        )
    if "Voce e o ATLAS" in sp:
        return SimpleNamespace(
            text='{"signal_type": "NEUTRAL", "confidence": 55, "summary": "atlas e2e"}',
            model="llama-e2e",
            provider="groq",
        )
    if "TrendsAgent" in sp:
        return SimpleNamespace(
            text='{"signal_type": "IGNORE", "confidence": 50, "summary": "trends e2e"}',
            model="llama-e2e",
            provider="groq",
        )
    if "FundamentalistAgent" in sp:
        return SimpleNamespace(
            text='{"signal_type": "FAIR", "confidence": 50, "summary": "fund e2e"}',
            model="llama-e2e",
            provider="groq",
        )
    if "Voce e o ARGUS" in sp:
        return SimpleNamespace(
            text='{"is_reversal_alert": false, "reversal_message": ""}',
            model="llama-e2e",
            provider="groq",
        )
    if "SentimentAgent" in sp:
        return SimpleNamespace(
            text='{"signal_type": "NEUTRAL", "confidence": 50, "summary": "sent e2e"}',
            model="llama-e2e",
            provider="groq",
        )
    raise AssertionError(f"e2e: prompt Groq nao mapeado: {sp[:160]!r}")


class AnalysisPipelineE2ETests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        os.environ["FEATURE_STORE_LOG_PATH"] = self.tmp.name
        os.environ.setdefault("AEGIS_ENABLE_DYNAMIC_RECALIBRATION", "false")

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def test_analyze_pipeline_exposes_agent_llm_provenance(self):
        from api.analysis_service import AnalysisService

        with (
            patch("requests.get", side_effect=_fake_requests_get),
            patch("agents.macro_agent.yf.Ticker", return_value=_FakeTicker()),
            patch("agents.atlas_agent.yf.Ticker", return_value=_FakeTicker()),
            patch("agents.trends_agent.yf.Ticker", return_value=_FakeTicker()),
            patch("agents.fundamentalist_agent.yf.Ticker", return_value=_FakeTicker()),
            patch.object(GroqClient, "complete", side_effect=_groq_complete_e2e),
        ):
            svc = AnalysisService()
            alert = svc.analyze("BTC-BRL", chart_timeframe="1h")

        self.assertTrue(alert.governance.approved)
        prov = alert.agent_llm_provenance
        self.assertIsNotNone(prov)
        self.assertIn("AEGIS", prov)
        self.assertIn("ATLAS", prov)
        self.assertIn("ORION", prov)
        self.assertEqual(prov["AEGIS"]["status"], "llm_success")
        self.assertEqual(prov["ORION"]["provider"], "groq")


class AnalysisPipelineE2EOrionSkippedTests(unittest.TestCase):
    """ORION sem RSS: provenance llm_skipped mas pipeline segue."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.tmp.close()
        os.environ["FEATURE_STORE_LOG_PATH"] = self.tmp.name
        os.environ.setdefault("AEGIS_ENABLE_DYNAMIC_RECALIBRATION", "false")

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def test_orion_skipped_when_rss_empty(self):
        from api.analysis_service import AnalysisService

        def empty_rss(url, timeout=10, **kwargs):
            if "news.google" in str(url):
                r = MagicMock()
                r.content = b'<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'
                r.raise_for_status = MagicMock()
                return r
            r = MagicMock()
            r.raise_for_status.side_effect = RuntimeError("bad")
            return r

        with (
            patch("requests.get", side_effect=empty_rss),
            patch("agents.macro_agent.yf.Ticker", return_value=_FakeTicker()),
            patch("agents.atlas_agent.yf.Ticker", return_value=_FakeTicker()),
            patch("agents.trends_agent.yf.Ticker", return_value=_FakeTicker()),
            patch("agents.fundamentalist_agent.yf.Ticker", return_value=_FakeTicker()),
            patch.object(GroqClient, "complete", side_effect=_groq_complete_e2e),
        ):
            svc = AnalysisService()
            alert = svc.analyze("BTC-BRL", chart_timeframe="1h")

        self.assertIsNotNone(alert.agent_llm_provenance)
        self.assertEqual(alert.agent_llm_provenance["ORION"]["status"], "llm_skipped")


if __name__ == "__main__":
    unittest.main()
