"""Despesas operacionais dedutíveis — metodologias documentadas."""

from __future__ import annotations

from typing import Dict


def calcular_despesa_energia(
    watts: float,
    horas_dia: float,
    dias_mes: int,
    tarifa_kwh_brl: float,
) -> Dict[str, object]:
    kwh_diario = (watts / 1000.0) * horas_dia
    kwh_mensal = kwh_diario * dias_mes
    custo_brl = round(kwh_mensal * tarifa_kwh_brl, 2)
    metodologia = (
        f"{watts}W × {horas_dia}h/dia × {dias_mes} dias "
        f"÷ 1000 = {kwh_mensal:.2f} kWh × R$ {tarifa_kwh_brl}/kWh"
    )
    return {
        "kwh_mensal": round(kwh_mensal, 2),
        "custo_brl": custo_brl,
        "metodologia": metodologia,
        "instrucao": "Arquivar junto à conta de energia do mês correspondente.",
    }
