"""Classificador determinista para comparativos de stress test.

Compara um cenario com risco filtrado vs cenario base e classifica o efeito.

`classify_comparison(drawdown_reduction_pct, net_profit_delta_pct)` retorna:
  - "RISK_FILTER_PROTECTIVE": o filtro reduziu drawdown de forma material
    sem destruir o lucro liquido.
  - "DETRIMENTAL": o filtro reduz/limita o drawdown, mas o lucro liquido
    cai alem do tolerado (perda de oportunidade alta).
  - "NEUTRAL": ganho marginal de drawdown e/ou impacto pequeno em lucro;
    nao justifica mudanca operacional.

Os limiares sao deterministicos e ajustaveis via variaveis de ambiente:
  STRESS_PROFIT_LOSS_LIMIT_PCT (default 20.0)
  STRESS_DRAWDOWN_REDUCTION_MIN_PCT (default 20.0)
"""

from __future__ import annotations

import os


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return float(default)
    return float(raw)


def classify_comparison(
    drawdown_reduction_pct: float,
    net_profit_delta_pct: float,
) -> str:
    """Classifica o efeito de um filtro de risco vs cenario base."""
    profit_loss_limit = _env_float("STRESS_PROFIT_LOSS_LIMIT_PCT", 20.0)
    dd_reduction_min = _env_float("STRESS_DRAWDOWN_REDUCTION_MIN_PCT", 20.0)

    if float(net_profit_delta_pct) <= -abs(profit_loss_limit):
        return "DETRIMENTAL"

    if float(drawdown_reduction_pct) >= abs(dd_reduction_min):
        return "RISK_FILTER_PROTECTIVE"

    return "NEUTRAL"


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 3:
        print(
            json.dumps(
                {
                    "error": "uso: python run_stress_test.py <drawdown_reduction_pct> <net_profit_delta_pct>",
                }
            )
        )
        sys.exit(2)

    dd = float(sys.argv[1])
    np_delta = float(sys.argv[2])
    print(
        json.dumps(
            {
                "drawdown_reduction_pct": dd,
                "net_profit_delta_pct": np_delta,
                "classification": classify_comparison(dd, np_delta),
            }
        )
    )
