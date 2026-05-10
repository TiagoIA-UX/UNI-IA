import os
import ccxt
from typing import Dict, Any

class MercadoBitcoinCCXTAdapter:
    def __init__(self):
        self.api_key = os.getenv('BROKER_API_KEY', '')
        self.api_secret = os.getenv('BROKER_API_SECRET', '')
        self.exchange = ccxt.mercadobitcoin({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })

    def is_ready(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def missing_config(self):
        missing = []
        if not self.api_key: missing.append('BROKER_API_KEY')
        if not self.api_secret: missing.append('BROKER_API_SECRET')
        return missing

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError("Configuração de API do Mercado Bitcoin ausente.")
        
        raw_symbol = payload.get('symbol', 'BTCUSDT').upper()
        symbol = raw_symbol.replace('USDT', '/BRL')
        side = payload.get('side', 'BUY').lower()
        qty = float(os.getenv('MB_DEFAULT_QTY', '0.0001'))

        try:
            return self.exchange.create_order(symbol=symbol, type='market', side=side, amount=qty)
        except Exception as e:
            raise RuntimeError(f"Erro na execução MB via CCXT: {str(e)}")
