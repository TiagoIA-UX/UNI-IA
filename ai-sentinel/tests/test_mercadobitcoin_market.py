import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from adapters.mercadobitcoin_market import compact_mb_market, get_ticker, normalize_mb_market
from agents.market_utils import resolve_market_ticker


class MercadoBitcoinMarketTests(unittest.TestCase):
    def test_normalize_mb_market_aliases(self):
        self.assertEqual(normalize_mb_market("BTC-BRL"), "BTC-BRL")
        self.assertEqual(normalize_mb_market("BTCBRL"), "BTC-BRL")
        self.assertEqual(normalize_mb_market("BTCUSDT"), "BTC-BRL")
        self.assertEqual(compact_mb_market("ETH-BRL"), "ETHBRL")

    def test_brl_crypto_uses_global_yfinance_context(self):
        self.assertEqual(resolve_market_ticker("BTCBRL"), "BTC-USD")
        self.assertEqual(resolve_market_ticker("ETH-BRL"), "ETH-USD")

    @patch("adapters.mercadobitcoin_market._get_json")
    def test_get_ticker_normalizes_public_payload(self, fake_get_json):
        fake_get_json.return_value = {"last": "398162.00", "high": "402340", "low": "394121", "volume": "25.66"}
        out = get_ticker("BTC-BRL")
        self.assertEqual(out["market"], "BTC-BRL")
        self.assertEqual(out["last"], 398162.0)
        self.assertEqual(out["high"], 402340.0)


if __name__ == "__main__":
    unittest.main()
