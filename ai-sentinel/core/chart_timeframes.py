"""Timeframes de grafico alinhados a yfinance + embed TradingView (widget).

Cada entrada define o intervalo canonico usado no motor (ATLAS / outcomes)
e o parametro `interval` do iframe TV onde aplicavel.

`agent_alignment` resume o peso relativo dos agentes neste TF, alinhado a
pratica de analise multi-timeframe (tendencia HTF > setup MTF > entrada LTF).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Ordem de exibicao na UI (do mais curto ao mais longo permitido neste produto).
_TIMEFRAME_ROWS: List[Dict[str, Any]] = [
    {
        "label": "M1",
        "canonical": "1m",
        "tv": "1",
        "hint": "Micro scalping — VWAP, volume, micro-estrutura",
        "agent_alignment": "ATLAS + ARGUS lideram execucao; MACRO/NEWS so como pano de fundo.",
        "strategy_family": "intraday_swings",
        "strategy_family_note": "ATLAS calcula HH/HL/LH/LL no proprio intervalo do grafico (topos/fundos locais).",
    },
    {
        "label": "M2",
        "canonical": "2m",
        "tv": "2",
        "hint": "Scalping rapido — ritmo curto, confirmação de fluxo",
        "agent_alignment": "Tecnico + volume dominam; sentimento macro com peso baixo.",
        "strategy_family": "intraday_swings",
        "strategy_family_note": "Mesma familia M1/M5: estrutura de swings no TF do grafico.",
    },
    {
        "label": "M5",
        "canonical": "5m",
        "tv": "5",
        "hint": "Scalping classico — medias curtas, bandas, momentum",
        "agent_alignment": "ATLAS central; ORION/NEWS apenas se catalisar volatilidade intradia.",
        "strategy_family": "intraday_swings",
        "strategy_family_note": "Estrutura swing no 5m + RSI/volume no mesmo TF.",
    },
    {
        "label": "M15",
        "canonical": "15m",
        "tv": "15",
        "hint": "Intraday — MACD, RSI 14, VWAP de sessao",
        "agent_alignment": "Equilibrio ATLAS + Trends; MACRO ainda filtro, nao gatilho unico.",
        "strategy_family": "intraday_swings",
        "strategy_family_note": "Transicao para swings intradiarios; mesma deteccao de topos/fundos no 15m.",
    },
    {
        "label": "M30",
        "canonical": "30m",
        "tv": "30",
        "hint": "Intraday swing — medias 20/50, menos ruido que M15",
        "agent_alignment": "Tecnico + regime; SENTIMENT/NEWS ganham relevancia moderada.",
        "strategy_family": "intraday_swings",
        "strategy_family_note": "Inclui estrutura swing no 30m quando dados yfinance forem suficientes.",
    },
    {
        "label": "H1",
        "canonical": "1h",
        "tv": "60",
        "hint": "Swing curto — tendencia intradia + estrutura",
        "agent_alignment": "ATLAS + AEGIS; MACRO e ORION passam a informar direcao com mais peso.",
        "strategy_family": "swing_intraday_htf",
        "strategy_family_note": "Estrutura no 1h + contexto diario (MAs/ATR 1d) no vetor ATLAS.",
    },
    {
        "label": "M90",
        "canonical": "90m",
        "tv": "90",
        "hint": "Sessao estendida — entre intraday e swing",
        "agent_alignment": "Mesma logica do H1 com menos ruido; boa ponte para HTF.",
        "strategy_family": "swing_intraday_htf",
        "strategy_family_note": "Similar ao H1.",
    },
    {
        "label": "H4",
        "canonical": "4h",
        "tv": "240",
        "hint": "Swing — estrutura HTF, momentum de posicao",
        "agent_alignment": "MACRO + ATLAS em confluencia; NOTICIAS para eventos, nao para cada vela.",
        "strategy_family": "swing_htf",
        "strategy_family_note": "Swing em 4h alinhado a tendencia diaria/semanal.",
    },
    {
        "label": "D1",
        "canonical": "1d",
        "tv": "D",
        "hint": "Posicao — regime, medias longas, gap de abertura vs dia anterior",
        "agent_alignment": "MACRO, Trends e Fundamentalista relevantes; ATLAS para timing/refino.",
        "strategy_family": "position_gap_session",
        "strategy_family_note": "ATLAS expoe daily_session_gap_pct e ratio vs ATR14 diario; filtro PTAX async (core/gap_filter) e legado MT5 (executor) nao estao no POST /api/analyze.",
    },
    {
        "label": "W1",
        "canonical": "1wk",
        "tv": "W",
        "hint": "Macro semanal — tendencia dominante do book",
        "agent_alignment": "Contexto MACRO dominante; tecnicos como confirmacao, nao sinal isolado.",
        "strategy_family": "macro_position",
        "strategy_family_note": "Contexto longo; execucao em TF menor.",
    },
    {
        "label": "MN1",
        "canonical": "1mo",
        "tv": "M",
        "hint": "Ciclo mensal — posicao longa, baixa rotacao",
        "agent_alignment": "Fundamental + macro + sentimento de longo prazo; execucao via TF menor.",
        "strategy_family": "macro_position",
        "strategy_family_note": "Contexto longo; execucao em TF menor.",
    },
    {
        "label": "Q1",
        "canonical": "3mo",
        "tv": "3M",
        "hint": "Contexto trimestral — benchmark de regime",
        "agent_alignment": "Visao institucional; sinais operacionais sempre descidos para TF menor.",
        "strategy_family": "macro_position",
        "strategy_family_note": "Benchmark de regime; sem regra de gap intradiario.",
    },
]

_CANONICAL_SET = frozenset(row["canonical"] for row in _TIMEFRAME_ROWS)

_ALIASES: Dict[str, str] = {
    "m1": "1m",
    "m2": "2m",
    "m5": "5m",
    "m15": "15m",
    "m30": "30m",
    "h1": "1h",
    "60": "1h",
    "m90": "90m",
    "90": "90m",
    "h4": "4h",
    "240": "4h",
    "d1": "1d",
    "d": "1d",
    "1d": "1d",
    "w1": "1wk",
    "1w": "1wk",
    "week": "1wk",
    "mn1": "1mo",
    "month": "1mo",
    "q1": "3mo",
    "3mo": "3mo",
}

# Periodos yfinance por intervalo (ATLAS) — conservadores para evitar erro de API.
YF_HISTORY_CONFIG: Dict[str, tuple[str, str]] = {
    "1m": ("1m", "3d"),
    "2m": ("2m", "3d"),
    "5m": ("5m", "7d"),
    "15m": ("15m", "12d"),
    "30m": ("30m", "30d"),
    "1h": ("1h", "60d"),
    "90m": ("90m", "60d"),
    "4h": ("4h", "120d"),
    "1d": ("1d", "730d"),
    "1wk": ("1wk", "5y"),
    "1mo": ("1mo", "max"),
    "3mo": ("3mo", "max"),
}


def public_timeframes_catalog() -> List[Dict[str, Any]]:
    """Lista para UI e documentacao OpenAPI."""
    out: List[Dict[str, Any]] = []
    for r in _TIMEFRAME_ROWS:
        item: Dict[str, Any] = {
            "label": str(r["label"]),
            "canonical": str(r["canonical"]),
            "tv": str(r["tv"]),
            "strategy_hint": str(r["hint"]),
            "agent_alignment": str(r.get("agent_alignment", "")),
        }
        if r.get("strategy_family"):
            item["strategy_family"] = str(r["strategy_family"])
        if r.get("strategy_family_note"):
            item["strategy_family_note"] = str(r["strategy_family_note"])
        out.append(item)
    return out


def normalize_chart_timeframe(raw: Optional[str]) -> Optional[str]:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().lower()
    if s in _CANONICAL_SET:
        return s
    if s in _ALIASES:
        cand = _ALIASES[s]
        if cand in _CANONICAL_SET:
            return cand
    return None


def yf_interval_period(canonical: str) -> Optional[tuple[str, str]]:
    return YF_HISTORY_CONFIG.get(canonical)


_ROW_BY_CANON: Dict[str, Dict[str, Any]] = {str(r["canonical"]): r for r in _TIMEFRAME_ROWS}

# Pesos base AEGIS (soma 1.0) alinhados ao default historico do agente.
DEFAULT_AEGIS_WEIGHTS: Dict[str, float] = {
    "ATLAS": 0.30,
    "ORION": 0.20,
    "MacroAgent": 0.15,
    "NewsAgent": 0.10,
    "TrendsAgent": 0.10,
    "FundamentalistAgent": 0.10,
    "SentimentAgent": 0.05,
}

_AEGIS_BY_STRATEGY_FAMILY: Dict[str, Dict[str, float]] = {
    "intraday_swings": {
        "ATLAS": 0.34,
        "ORION": 0.22,
        "MacroAgent": 0.12,
        "NewsAgent": 0.08,
        "TrendsAgent": 0.16,
        "FundamentalistAgent": 0.04,
        "SentimentAgent": 0.04,
    },
    "swing_intraday_htf": {
        "ATLAS": 0.30,
        "ORION": 0.20,
        "MacroAgent": 0.16,
        "NewsAgent": 0.10,
        "TrendsAgent": 0.12,
        "FundamentalistAgent": 0.08,
        "SentimentAgent": 0.04,
    },
    "swing_htf": {
        "ATLAS": 0.26,
        "ORION": 0.18,
        "MacroAgent": 0.20,
        "NewsAgent": 0.12,
        "TrendsAgent": 0.10,
        "FundamentalistAgent": 0.10,
        "SentimentAgent": 0.04,
    },
    "position_gap_session": {
        "ATLAS": 0.24,
        "ORION": 0.16,
        "MacroAgent": 0.18,
        "NewsAgent": 0.12,
        "TrendsAgent": 0.12,
        "FundamentalistAgent": 0.14,
        "SentimentAgent": 0.04,
    },
    "macro_position": {
        "ATLAS": 0.20,
        "ORION": 0.14,
        "MacroAgent": 0.24,
        "NewsAgent": 0.12,
        "TrendsAgent": 0.08,
        "FundamentalistAgent": 0.18,
        "SentimentAgent": 0.04,
    },
}


def _assert_unit_weights(weights: Dict[str, float], label: str) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise RuntimeError(f"pesos AEGIS invalidos em {label}: soma={total}")


_assert_unit_weights(DEFAULT_AEGIS_WEIGHTS, "DEFAULT_AEGIS_WEIGHTS")
for _fam, _w in _AEGIS_BY_STRATEGY_FAMILY.items():
    _assert_unit_weights(_w, _fam)


def timeframe_strategy_legenda(canonical: Optional[str]) -> str:
    """Texto curto para injetar nos prompts dos agentes (alinhamento por TF)."""
    if not canonical:
        return (
            "Timeframe operacional: nao especificado. Trate como contexto neutro; "
            "nao assuma scalping nem posicao longa; priorize confluencia ATLAS/ORION com conservadorismo."
        )
    row = _ROW_BY_CANON.get(canonical)
    if not row:
        return (
            f"Timeframe operacional canonico desconhecido: {canonical!r}. "
            "Nao invente dados; alinhe o raciocinio ao que o vetor de features suporta."
        )
    parts = [
        f"Timeframe operacional do cliente: {row['label']} ({canonical}).",
        f"Familia de estrategia: {row.get('strategy_family', '')}.",
        f"Dica pratica: {row.get('hint', '')}.",
        f"Alinhamento multi-agente esperado: {row.get('agent_alignment', '')}.",
    ]
    note = row.get("strategy_family_note")
    if note:
        parts.append(str(note))
    return " ".join(parts)


def aegis_base_weights_for_chart_timeframe(canonical: Optional[str]) -> Dict[str, float]:
    """Pesos base AEGIS conforme familia de estrategia do timeframe canonico."""
    if not canonical or canonical not in _ROW_BY_CANON:
        return dict(DEFAULT_AEGIS_WEIGHTS)
    fam = str(_ROW_BY_CANON[canonical].get("strategy_family") or "")
    tpl = _AEGIS_BY_STRATEGY_FAMILY.get(fam)
    if not tpl:
        return dict(DEFAULT_AEGIS_WEIGHTS)
    return dict(tpl)
