"""NAO — Nota de Apuração (documento interno DOC, não NF-e PJ)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


REFERENCIAS_LEGAIS_TEXTO_CONSOLIDADO = """IN RFB 1.888/2019 · Lei 9.250/1995 · Lei 9.532/1997 ·
IN RFB 1.585/2015 · IN RFB 1.500/2014 · Res. BACEN 4.935/2021 · LC 179/2021 ·
Lei 8.069/1990 (ECA) · Lei 8.242/1991 — consolidado referencial"""


@dataclass
class NAO:
    numero_sequencial: str
    periodo_referencia: str
    data_geracao_utc: str
    hash_documento: str

    nome_completo: str
    cpf: str
    endereco_completo: str
    atividade: str = "Pessoa Física — Ganhos de Capital em Criptoativos (modelo doc)"

    exchange_utilizada: str = ""
    autorizacao_bacen: str = ""

    receita_bruta_dt: float = 0.0
    taxas_comprovadas_dt: float = 0.0
    prejuizo_compensado_dt: float = 0.0
    base_calculo_dt: float = 0.0
    ir_apurado_dt: float = 0.0
    codigo_darf_dt: str = "4600"

    volume_vendido_st: float = 0.0
    receita_bruta_st: float = 0.0
    taxas_comprovadas_st: float = 0.0
    prejuizo_compensado_st: float = 0.0
    base_calculo_st: float = 0.0
    isento_st: bool = False
    ir_apurado_st: float = 0.0
    codigo_darf_st: str = "6015"

    total_despesas_comprovadas: float = 0.0
    detalhamento_despesas: List[dict] = field(default_factory=list)

    fca_6pct_ir_devido: float = 0.0
    reserva_animal_consciente: float = 0.0
    flag_animal_status: str = ""

    versao_software: str = "boitata-doc-0.1"
    agentes_operadores: List[str] = field(default_factory=list)
    referencias_legais: str = REFERENCIAS_LEGAIS_TEXTO_CONSOLIDADO

    def conteudo_para_hash(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        for k, v in self.__dict__.items():
            if k == "hash_documento":
                continue
            d[k] = v
        return d

    @staticmethod
    def calcular_hash(doc_dict: Dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(doc_dict, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()


def montar_nao_de_apuracao(
    *,
    periodo: str,
    seq: int,
    operador: Dict[str, str],
    resultado_mes: Dict[str, Any],
    exchange: str,
    bacen_ref: str,
    despesas: Optional[List[dict]] = None,
    agentes: Optional[List[str]] = None,
) -> NAO:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    nao = NAO(
        numero_sequencial=f"NAO-{periodo}-{seq:04d}",
        periodo_referencia=periodo,
        data_geracao_utc=now,
        hash_documento="",
        nome_completo=operador.get("nome", ""),
        cpf=operador.get("cpf", ""),
        endereco_completo=operador.get("endereco", ""),
        exchange_utilizada=exchange,
        autorizacao_bacen=bacen_ref,
        ir_apurado_dt=float(resultado_mes.get("ir_day_trade", 0)),
        ir_apurado_st=float(resultado_mes.get("ir_swing_trade", 0)),
        volume_vendido_st=float(resultado_mes.get("volume_vendido_swing", 0)),
        isento_st=bool(resultado_mes.get("isento_swing")),
        fca_6pct_ir_devido=float(resultado_mes.get("fca_6pct", 0)),
        reserva_animal_consciente=float(resultado_mes.get("reserva_animal_consciente", 0)),
        flag_animal_status=str(resultado_mes.get("flag_animal_status", "")),
        detalhamento_despesas=list(despesas or []),
        agentes_operadores=list(agentes or ["DOC-module"]),
    )
    nao.hash_documento = NAO.calcular_hash(nao.conteudo_para_hash())
    return nao


def serializar_nao(n: NAO) -> Dict[str, Any]:
    d = dict(n.__dict__)
    return d
