"""ATLAS — Agente Estrutural Tecnico.

ATLAS nao le noticia. ATLAS nao interpreta macro.
ATLAS le estrutura e fluxo.

Features computadas (nao opinadas):
  - Market structure: HH/HL/LH/LL detection
  - Break of structure (BOS)
  - ATR regime (volatilidade normalizada)
  - Volume profile (VWAP, volume anomaly, relative volume)
  - Multi-timeframe momentum (RSI, MACD cross)
  - Support/resistance key levels
  - Trend strength (ADX proxy via DI+/DI-)

Todas as features sao numericas e persistidas no FeatureStore.
A LLM e chamada APENAS para interpretar o vetor numerico final,
nunca para gerar os numeros.
"""

import math
from typing import Any, Dict, Optional

import yfinance as yf
import numpy as np

from agents.market_utils import resolve_market_ticker
from core.feature_store import FeatureStore
from core.schemas import AgentSignal
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object


def _safe(val: Any, decimals: int = 6) -> Any:
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if isinstance(val, (float, np.floating)):
        return round(float(val), decimals)
    if isinstance(val, (int, np.integer)):
        return int(val)
    return val


class AtlasAgent:
    """Agente Estrutural Tecnico — ATLAS."""

    def __init__(self, feature_store: Optional[FeatureStore] = None):
        self.llm = GroqClient()
        self.feature_store = feature_store or FeatureStore()
        self.system_prompt = """Voce e o ATLAS, agente estrutural tecnico do Zairyx IA.
Voce recebe um VETOR NUMERICO de features de mercado ja calculadas.
Sua funcao e interpretar esse vetor e emitir um julgamento estrutural.

Regras:
1. NUNCA invente numeros. Use APENAS os fornecidos.
2. Analise a confluencia entre timeframes.
3. Identifique se a estrutura permite risco (entrada) ou nao.

Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "signal_type": "STRONG BUY" ou "BUY" ou "NEUTRAL" ou "SELL" ou "STRONG SELL",
    "confidence": 85.5,
    "summary": "Interpretacao estrutural objetiva baseada nas features."
}"""

    def _get_ticker(self, asset: str) -> str:
        return resolve_market_ticker(asset)

    # ------------------------------------------------------------------
    # Feature computation (puro numpy, zero LLM)
    # ------------------------------------------------------------------

    def compute_features(self, asset: str) -> Dict[str, Any]:
        """Computa vetor completo de features estruturais."""
        ticker_str = self._get_ticker(asset)
        ticker = yf.Ticker(ticker_str)

        # Multi-timeframe data
        hist_1d = ticker.history(period="3mo", interval="1d")
        hist_1h = ticker.history(period="5d", interval="1h")
        hist_15m = ticker.history(period="5d", interval="15m")

        if hist_1d.empty or len(hist_1d) < 20:
            raise ValueError(f"Dados insuficientes para ATLAS computar features de {asset}.")

        features: Dict[str, Any] = {"asset": asset}

        # --- Price basics ---
        close_1d = hist_1d["Close"].values
        high_1d = hist_1d["High"].values
        low_1d = hist_1d["Low"].values
        volume_1d = hist_1d["Volume"].values

        features["price_last"] = _safe(close_1d[-1])
        features["price_prev_close"] = _safe(close_1d[-2]) if len(close_1d) > 1 else None
        features["daily_return_pct"] = _safe((close_1d[-1] / close_1d[-2] - 1) * 100) if len(close_1d) > 1 else None

        # --- Moving Averages ---
        for window in [7, 20, 50]:
            if len(close_1d) >= window:
                ma = float(np.mean(close_1d[-window:]))
                features[f"ma_{window}_1d"] = _safe(ma)
                features[f"ma_{window}_1d_dist_pct"] = _safe((close_1d[-1] / ma - 1) * 100)
            else:
                features[f"ma_{window}_1d"] = None
                features[f"ma_{window}_1d_dist_pct"] = None

        # --- ATR (14 periodos) ---
        atr_period = 14
        if len(high_1d) >= atr_period + 1:
            tr_list = []
            for i in range(-atr_period, 0):
                tr = max(
                    high_1d[i] - low_1d[i],
                    abs(high_1d[i] - close_1d[i - 1]),
                    abs(low_1d[i] - close_1d[i - 1]),
                )
                tr_list.append(tr)
            atr = float(np.mean(tr_list))
            features["atr_14_1d"] = _safe(atr)
            features["atr_14_1d_pct"] = _safe((atr / close_1d[-1]) * 100) if close_1d[-1] != 0 else None
        else:
            features["atr_14_1d"] = None
            features["atr_14_1d_pct"] = None

        # --- ATR Regime (low / normal / high / extreme) ---
        if features["atr_14_1d_pct"] is not None:
            atr_pct = features["atr_14_1d_pct"]
            if atr_pct < 1.0:
                features["atr_regime"] = "low"
            elif atr_pct < 3.0:
                features["atr_regime"] = "normal"
            elif atr_pct < 6.0:
                features["atr_regime"] = "high"
            else:
                features["atr_regime"] = "extreme"
        else:
            features["atr_regime"] = None

        # --- RSI (14 periodos) ---
        rsi_period = 14
        if len(close_1d) >= rsi_period + 1:
            deltas = np.diff(close_1d[-(rsi_period + 1):])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = float(np.mean(gains))
            avg_loss = float(np.mean(losses))
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100.0 - (100.0 / (1.0 + rs))
            features["rsi_14_1d"] = _safe(rsi, 2)
        else:
            features["rsi_14_1d"] = None

        # --- MACD (12, 26, 9) ---
        if len(close_1d) >= 26:
            ema_12 = self._ema(close_1d, 12)
            ema_26 = self._ema(close_1d, 26)
            macd_line = ema_12 - ema_26
            if len(close_1d) >= 35:
                signal_line = self._ema_from_series(
                    np.array([self._ema(close_1d[:i + 1], 12) - self._ema(close_1d[:i + 1], 26) for i in range(25, len(close_1d))]),
                    9,
                )
                features["macd_line"] = _safe(macd_line)
                features["macd_signal"] = _safe(signal_line)
                features["macd_histogram"] = _safe(macd_line - signal_line)
                features["macd_cross"] = "bullish" if macd_line > signal_line else "bearish"
            else:
                features["macd_line"] = _safe(macd_line)
                features["macd_signal"] = None
                features["macd_histogram"] = None
                features["macd_cross"] = None
        else:
            features["macd_line"] = None
            features["macd_signal"] = None
            features["macd_histogram"] = None
            features["macd_cross"] = None

        # --- Volume Profile ---
        if len(volume_1d) >= 10:
            vol_last = float(volume_1d[-1])
            vol_avg_10 = float(np.mean(volume_1d[-11:-1]))
            features["volume_last"] = _safe(vol_last, 0)
            features["volume_avg_10d"] = _safe(vol_avg_10, 0)
            features["volume_ratio"] = _safe(vol_last / vol_avg_10) if vol_avg_10 > 0 else None
            features["volume_anomaly"] = (vol_last / vol_avg_10) > 2.0 if vol_avg_10 > 0 else False
        else:
            features["volume_last"] = None
            features["volume_avg_10d"] = None
            features["volume_ratio"] = None
            features["volume_anomaly"] = None

        # --- VWAP (intraday from 1h data) ---
        if not hist_1h.empty and len(hist_1h) >= 5:
            typical_price = (hist_1h["High"].values + hist_1h["Low"].values + hist_1h["Close"].values) / 3.0
            vol_1h = hist_1h["Volume"].values.astype(float)
            cumvol = np.cumsum(vol_1h)
            cum_tp_vol = np.cumsum(typical_price * vol_1h)
            vwap_val = float(cum_tp_vol[-1] / cumvol[-1]) if cumvol[-1] > 0 else None
            features["vwap_1h"] = _safe(vwap_val)
            if vwap_val and vwap_val != 0:
                features["vwap_1h_dist_pct"] = _safe((close_1d[-1] / vwap_val - 1) * 100)
            else:
                features["vwap_1h_dist_pct"] = None
        else:
            features["vwap_1h"] = None
            features["vwap_1h_dist_pct"] = None

        # --- Market Structure: HH/HL/LH/LL detection ---
        structure = self._detect_market_structure(high_1d, low_1d)
        features["structure_pattern"] = structure["pattern"]
        features["structure_trend"] = structure["trend"]
        features["structure_bos"] = structure["bos"]
        features["structure_swing_high"] = _safe(structure["swing_high"])
        features["structure_swing_low"] = _safe(structure["swing_low"])

        # --- Support / Resistance (pivot-based) ---
        if len(high_1d) >= 3:
            pivot = (float(high_1d[-2]) + float(low_1d[-2]) + float(close_1d[-2])) / 3.0
            features["pivot_point"] = _safe(pivot)
            features["resistance_1"] = _safe(2 * pivot - float(low_1d[-2]))
            features["support_1"] = _safe(2 * pivot - float(high_1d[-2]))
            features["resistance_2"] = _safe(pivot + (float(high_1d[-2]) - float(low_1d[-2])))
            features["support_2"] = _safe(pivot - (float(high_1d[-2]) - float(low_1d[-2])))
        else:
            features["pivot_point"] = None
            features["resistance_1"] = None
            features["support_1"] = None
            features["resistance_2"] = None
            features["support_2"] = None

        # --- 1H momentum (RSI 1h) ---
        if not hist_1h.empty and len(hist_1h) >= 15:
            close_1h = hist_1h["Close"].values
            deltas_1h = np.diff(close_1h[-15:])
            g = np.where(deltas_1h > 0, deltas_1h, 0)
            l = np.where(deltas_1h < 0, -deltas_1h, 0)
            ag = float(np.mean(g))
            al = float(np.mean(l))
            if al == 0:
                rsi_1h = 100.0
            else:
                rsi_1h = 100.0 - (100.0 / (1.0 + ag / al))
            features["rsi_14_1h"] = _safe(rsi_1h, 2)
        else:
            features["rsi_14_1h"] = None

        # --- 15m micro-structure ---
        if not hist_15m.empty and len(hist_15m) >= 10:
            close_15m = hist_15m["Close"].values
            features["price_15m_last"] = _safe(close_15m[-1])
            features["price_15m_change_5bars_pct"] = _safe(
                (close_15m[-1] / close_15m[-6] - 1) * 100
            ) if len(close_15m) >= 6 else None
        else:
            features["price_15m_last"] = None
            features["price_15m_change_5bars_pct"] = None

        # --- Divergence RSI vs Price (simple) ---
        if features.get("rsi_14_1d") is not None and len(close_1d) >= 28:
            price_rising = close_1d[-1] > close_1d[-14]
            # Compute RSI 14 bars ago
            deltas_prev = np.diff(close_1d[-(rsi_period + 15):-(rsi_period + 1)])
            if len(deltas_prev) == rsi_period:
                g_prev = np.where(deltas_prev > 0, deltas_prev, 0)
                l_prev = np.where(deltas_prev < 0, -deltas_prev, 0)
                ag_prev = float(np.mean(g_prev))
                al_prev = float(np.mean(l_prev))
                rsi_prev = 100.0 if al_prev == 0 else 100.0 - (100.0 / (1.0 + ag_prev / al_prev))
                rsi_rising = features["rsi_14_1d"] > rsi_prev

                if price_rising and not rsi_rising:
                    features["divergence_rsi_1d"] = "bearish"
                elif not price_rising and rsi_rising:
                    features["divergence_rsi_1d"] = "bullish"
                else:
                    features["divergence_rsi_1d"] = "none"
            else:
                features["divergence_rsi_1d"] = None
        else:
            features["divergence_rsi_1d"] = None

        return features

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _ema(self, data: np.ndarray, period: int) -> float:
        if len(data) < period:
            return float(np.mean(data))
        multiplier = 2.0 / (period + 1)
        ema_val = float(np.mean(data[:period]))
        for price in data[period:]:
            ema_val = (float(price) - ema_val) * multiplier + ema_val
        return ema_val

    def _ema_from_series(self, data: np.ndarray, period: int) -> float:
        return self._ema(data, period)

    def _detect_market_structure(self, highs: np.ndarray, lows: np.ndarray) -> Dict[str, Any]:
        """Detecta HH/HL/LH/LL e Break of Structure."""
        result: Dict[str, Any] = {
            "pattern": "undefined",
            "trend": "undefined",
            "bos": False,
            "swing_high": None,
            "swing_low": None,
        }

        if len(highs) < 10:
            return result

        # Find swing points (simplified: local extremes over 5-bar window)
        swing_highs = []
        swing_lows = []
        for i in range(2, len(highs) - 2):
            if highs[i] >= max(highs[i - 2], highs[i - 1], highs[i + 1], highs[i + 2]):
                swing_highs.append((i, float(highs[i])))
            if lows[i] <= min(lows[i - 2], lows[i - 1], lows[i + 1], lows[i + 2]):
                swing_lows.append((i, float(lows[i])))

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return result

        last_sh = swing_highs[-1][1]
        prev_sh = swing_highs[-2][1]
        last_sl = swing_lows[-1][1]
        prev_sl = swing_lows[-2][1]

        result["swing_high"] = last_sh
        result["swing_low"] = last_sl

        hh = last_sh > prev_sh
        hl = last_sl > prev_sl
        lh = last_sh < prev_sh
        ll = last_sl < prev_sl

        if hh and hl:
            result["pattern"] = "HH+HL"
            result["trend"] = "bullish"
        elif lh and ll:
            result["pattern"] = "LH+LL"
            result["trend"] = "bearish"
        elif hh and ll:
            result["pattern"] = "HH+LL"
            result["trend"] = "expansion"
        elif lh and hl:
            result["pattern"] = "LH+HL"
            result["trend"] = "compression"
        else:
            result["pattern"] = "mixed"
            result["trend"] = "neutral"

        # BOS: preco atual rompeu ultimo swing high ou low
        current_close = float(highs[-1])  # approximate with last high
        if current_close > last_sh:
            result["bos"] = True
        elif float(lows[-1]) < last_sl:
            result["bos"] = True

        return result

    # ------------------------------------------------------------------
    # Analise completa
    # ------------------------------------------------------------------

    def analyze(self, asset: str, signal_id: Optional[str] = None) -> AgentSignal:
        """Computa features, persiste, interpreta via LLM."""
        features = self.compute_features(asset)

        # Montar prompt com features numericas
        feature_text = self._format_features(features)
        prompt = f"Vetor de features estruturais para {asset}:\n\n{feature_text}\n\nInterprete a estrutura e emita seu julgamento."

        response = self.llm.generate_response(self.system_prompt, prompt)
        data = extract_json_object(response)

        if signal_id:
            self.feature_store.persist(
                signal_id=signal_id,
                asset=asset,
                agent_name="ATLAS",
                features={
                    **features,
                    "emitted_confidence": float(data["confidence"]),
                },
                metadata={
                    "signal_type": data["signal_type"],
                    "summary": data["summary"],
                },
            )

        return AgentSignal(
            agent_name="ATLAS",
            asset=asset,
            signal_type=data["signal_type"],
            confidence=float(data["confidence"]),
            summary=data["summary"],
            raw_data=feature_text,
        )

    def _format_features(self, features: Dict[str, Any]) -> str:
        lines = []
        for key, val in features.items():
            if key == "asset":
                continue
            if val is None:
                continue
            lines.append(f"  {key}: {val}")
        return "\n".join(lines)
