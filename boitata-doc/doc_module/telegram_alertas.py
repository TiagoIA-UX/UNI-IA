"""Alertas Telegram (templates + envio opcional)."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Optional

from doc_module.apuracao_fiscal import LIMIAR_ISENCAO_SWING


def nivel1_alerta(volume: float, mes: int, ano: int) -> str:
    saldo = max(LIMIAR_ISENCAO_SWING - volume, 0.0)
    pct = min(100.0, volume / LIMIAR_ISENCAO_SWING * 100.0)
    return json.dumps(
        {
            "nivel": 1,
            "titulo": "BOITATÁ IA — Alerta Fiscal",
            "periodo": f"{mes:02d}/{ano}",
            "volume_swing_vendido_brl": round(volume, 2),
            "limite_isencao_brl": LIMIAR_ISENCAO_SWING,
            "saldo_ate_limite_brl": round(saldo, 2),
            "pct_utilizado": round(pct, 2),
            "recomendacao": "Considerar pausar novas saídas Swing ou aguardar virada do mês.",
            "referencia_documental": "Lei 9.250/1995 art. 22 §1º — conferir interpretação atual com contador",
        },
        ensure_ascii=False,
        indent=2,
    )


def nivel2_bloqueio(volume: float, mes: int, ano: int, data_vencimento_ref: str) -> str:
    return json.dumps(
        {
            "nivel": 2,
            "titulo": "BOITATÁ IA — Limite de isenção (volume)",
            "periodo": f"{mes:02d}/{ano}",
            "volume_vendido_brl": round(volume, 2),
            "darf_codigo_doc": "6015",
            "vencimento_referencia": data_vencimento_ref,
            "politica_swing_doc": "Bloquear novas saídas até revisão mensal.",
            "aviso": "Modelo técnico; não substitui cálculo fiscal oficial.",
        },
        ensure_ascii=False,
        indent=2,
    )


def reset_mensal(mes: int, ano: int, ts_utc: str) -> str:
    return json.dumps(
        {
            "evento": "reset_periodo",
            "periodo_ativo": f"{mes:02d}/{ano}",
            "volume_swing_acumulado_brl": 0.0,
            "timestamp_utc": ts_utc,
        },
        ensure_ascii=False,
        indent=2,
    )


def enviar_telegram_json(corpo_json: str, *, token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    """Plain text Markdown desligado — envia mensagem texto com JSON legível."""
    tok = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not tok or not cid:
        return False
    data = urllib.parse.urlencode({"chat_id": cid, "text": corpo_json[:3500]}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status == 200
