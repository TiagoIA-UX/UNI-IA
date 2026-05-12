"""
Regras de timeframe declarativas para *política* DOC (não bloqueiam o motor trading).

Este módulo permite que integrações futuras registrem qual TF foi usado e se estava de acordo com
a política interna DOC — apenas metadados; sem efeitos no ai-sentinel.
"""

from __future__ import annotations

from typing import Dict, List, TypedDict


class TfPolicy(TypedDict):
    permite_day: bool
    permite_swing: bool
    nota: str


# Chaves iguais às etiquetas típicas UI (ajustável)
DOC_TF_POLICY: Dict[str, TfPolicy] = {
    "M1": {"permite_day": True, "permite_swing": False, "nota": "estrutura intraday"},
    "M5": {"permite_day": True, "permite_swing": False, "nota": "estrutura intraday"},
    "M15": {"permite_day": True, "permite_swing": False, "nota": "estrutura intraday"},
    "M30": {"permite_day": True, "permite_swing": False, "nota": "estrutura intraday"},
    "H1": {"permite_day": True, "permite_swing": True, "nota": "swing apenas com trava DOC"},
    "H4": {"permite_day": True, "permite_swing": True, "nota": "monitorar day residual"},
    "D1": {"permite_day": False, "permite_swing": True, "nota": "contexto swing"},
    "W1": {"permite_day": False, "permite_swing": True, "nota": "macro"},
    "MN1": {"permite_day": False, "permite_swing": True, "nota": "referência — só leitura metadados"},
}


def politica_tf(label: str) -> TfPolicy:
    return DOC_TF_POLICY.get(label.upper(), {"permite_day": True, "permite_swing": True, "nota": "não catalogado"})
