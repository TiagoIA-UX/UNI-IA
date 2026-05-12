"""Apuração fiscal mensal e classificação determinística (sem LLM)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, TypedDict

LIMIAR_ISENCAO_SWING = 35_000.00
LIMIAR_ALERTA_80 = 28_000.00


class ClassificacaoOp(TypedDict):
    categoria: str
    aliquota: float
    isencao: bool
    codigo_darf: str
    base_legal: str


def classificar_operacao_fechada(
    data_abertura: datetime,
    data_fechamento: datetime,
    *,
    volume_vendido_mes_brl: float,
) -> ClassificacaoOp:
    """
    `volume_vendido_mes_brl` = soma das vendas (saídas) SWING no mês **incluindo** a operação corrente,
    para decisão de isenção no swing (conforme desenho do documento de arquitetura DOC).
    """
    mesma_data = data_abertura.date() == data_fechamento.date()
    if mesma_data:
        return {
            "categoria": "DAY_TRADE",
            "aliquota": 0.20,
            "isencao": False,
            "codigo_darf": "4600",
            "base_legal": "Lei 9.532/1997 art. 17 · IN RFB 1.585/2015",
        }
    isento = volume_vendido_mes_brl <= LIMIAR_ISENCAO_SWING
    return {
        "categoria": "SWING_TRADE",
        "aliquota": 0.0 if isento else 0.15,
        "isencao": isento,
        "codigo_darf": "6015",
        "base_legal": "Lei 9.250/1995 art. 22 §1º · IN RFB 1.585/2015",
    }


FLAG_FCA_6PCT = True
FCA_PERCENTUAL = 0.06
FLAG_PROTECAO_ANIMAL_CONSCIENTE = False


def apurar_mes(
    entradas_fechadas: List[Any],
    carry_forward_dt: float,
    carry_forward_st: float,
) -> Dict[str, Any]:
    """
    Args:
      entradas_fechadas: objetos com .categoria, .lucro_liquido_brl, .saida_brl
      carry_*: valores negativos = prejuízo a absorver
    """
    lucro_dt = sum(
        float(e.lucro_liquido_brl or 0)
        for e in entradas_fechadas
        if getattr(e, "categoria", None) == "DAY_TRADE"
    )
    lucro_st = sum(
        float(e.lucro_liquido_brl or 0)
        for e in entradas_fechadas
        if getattr(e, "categoria", None) == "SWING_TRADE"
    )
    volume_vendido_st = sum(
        float(e.saida_brl or 0)
        for e in entradas_fechadas
        if getattr(e, "categoria", None) == "SWING_TRADE"
    )

    def aplicar_carry(lucro: float, cf: float) -> float:
        pool = lucro + (cf if cf < 0 else 0)
        return max(0.0, pool)

    base_dt = aplicar_carry(lucro_dt, carry_forward_dt)
    base_st_raw = aplicar_carry(lucro_st, carry_forward_st)
    isento_st = volume_vendido_st <= LIMIAR_ISENCAO_SWING

    ir_dt = round(base_dt * 0.20, 2) if base_dt > 0 else 0.0
    ir_st = round(base_st_raw * 0.15, 2) if (base_st_raw > 0 and not isento_st) else 0.0

    ir_total = ir_dt + ir_st
    fca_dest = round(ir_total * FCA_PERCENTUAL, 2) if FLAG_FCA_6PCT else 0.0
    ir_liquido = round(ir_total - fca_dest, 2)

    def saldo_prejuizo(lucro: float) -> float:
        return min(0.0, float(lucro))

    reserva_animal = (
        round(lucro_st * 0.06, 2) if FLAG_PROTECAO_ANIMAL_CONSCIENTE else 0.0
    )

    return {
        "ir_day_trade": ir_dt,
        "ir_swing_trade": ir_st,
        "ir_total_devido": ir_total,
        "fca_6pct": fca_dest,
        "ir_liquido_a_pagar": ir_liquido,
        "isento_swing": isento_st,
        "volume_vendido_swing": round(volume_vendido_st, 2),
        "carry_forward_dt_proximo_mes": saldo_prejuizo(lucro_dt),
        "carry_forward_st_proximo_mes": saldo_prejuizo(lucro_st),
        "reserva_animal_consciente": reserva_animal,
        "flag_animal_status": (
            "ATIVO — dedução somente conforme lei em vigor"
            if FLAG_PROTECAO_ANIMAL_CONSCIENTE
            else "INATIVO — aguardando PL/regulamentação aplicável ao modelo doc"
        ),
    }
