import json
import re
import yfinance as yf
from ..core.schemas import AgentSignal
from ..llm.groq_client import GroqClient

class MacroAgent:
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = """
        Você é o MacroAgent. Avalie os DADOS REAIS DE MERCADO E COTAÇÃO.
        Identifique o ambiente Risk-On (Apetite a risco) ou Risk-Off (Aversão a risco) do ativo.
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "signal_type": "RISK-ON" ou "RISK-OFF" ou "NEUTRAL",
            "confidence": 75.0,
            "summary": "Análise focada em performance percentual de longo e curto prazo e aversão ao risco."
        }
        """
        
    def _get_ticker(self, asset: str) -> str:
        asset = asset.upper().strip()
        if asset == "USD": return "USDBRL=X"
        if asset == "EUR": return "EURBRL=X"
        if asset == "BRL": return "^BVSP" # IBOVESPA 
        if not asset.endswith(".SA") and not asset.endswith("=X") and not asset.startswith("^"):
            return f"{asset}.SA"
        return asset

    def fetch_real_market_data(self, asset: str) -> str:
        ticker_str = self._get_ticker(asset)
        ticker = yf.Ticker(ticker_str)
        
        info = ticker.info # Buscar real infos
        if not info or 'regularMarketPrice' not in info and 'currentPrice' not in info and 'previousClose' not in info:
             # Tento baixar histórico para extrair o dado de fechamento (para casos que info fica vazio em moedas via yf)
             hist = ticker.history(period="5d")
             if hist.empty:
                  raise ValueError(f"Não há dados recentes de mercado reais em bolsa para o ativo {asset} ({ticker_str}) via YFinance.")
             info = {
                 "currentPrice": hist["Close"].iloc[-1],
                 "previousClose": hist["Close"].iloc[-2],
                 "volume": hist["Volume"].iloc[-1]
             }

        price = info.get("currentPrice") or info.get("regularMarketPrice") or getattr(ticker.fast_info, 'last_price', None)
        prev_close = info.get("previousClose") or getattr(ticker.fast_info, 'previous_close', None)
        
        if not price or not prev_close:
             raise ValueError(f"Dados de preço incompletos para {asset} no provedor de mercado YFinance.")
             
        variation = ((price - prev_close) / prev_close) * 100
        
        market_stats = f"Ativo: {asset} (Ticker: {ticker_str})\n"
        market_stats += f"Preço Atual (Real-time): {price}\n"
        market_stats += f"Fechamento Anterior: {prev_close}\n"
        market_stats += f"Variação Diária: {variation:.2f}%\n"
        market_stats += f"Volume Recente: {info.get('volume', 'Desconhecido')}\n"
        
        return market_stats

    def analyze_macro_context(self, asset: str) -> AgentSignal:
        real_data = self.fetch_real_market_data(asset)
        
        prompt = f"Avalie a variação percentual de mercado HOJE (Agors) para o ativo {asset} com base nos dados brutos reais de tela:\n{real_data}"
        
        response = self.llm.generate_response(self.system_prompt, prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            raise ValueError(f"Groq não retornou JSON em MacroAgent. Resposta: {response}")
            
        data = json.loads(json_match.group(0))
        
        return AgentSignal(
            agent_name="MacroAgent",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=real_data
        )
