"""Núcleo: registo de operações, hash SHA-256, classificação alta-nível, whitelist BACEN."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from typing import Any, Dict, Literal, Optional

from doc_module.apuracao_fiscal import classificar_operacao_fechada

logger = logging.getLogger(__name__)

ExchangeCode = Literal[
    "MERCADO_BITCOIN",
    "FOXBIT",
    "BITSO_BR",
    "NOVADAX",
]

EXCHANGES_AUTORIZADAS: Dict[str, Dict[str, str]] = {
    "MERCADO_BITCOIN": {
        "nome": "Mercado Bitcoin",
        "regulacao": "BACEN — Res. 4.935/2021",
        "pais": "Brasil",
        "url_api": "https://api.mercadobitcoin.net/api/v4",
    },
    "FOXBIT": {
        "nome": "Foxbit",
        "regulacao": "BACEN — Res. 4.935/2021",
        "pais": "Brasil",
    },
    "BITSO_BR": {
        "nome": "Bitso Brasil",
        "regulacao": "BACEN — Res. 4.935/2021",
        "pais": "Brasil",
    },
    "NOVADAX": {
        "nome": "NovaDAX",
        "regulacao": "BACEN — Res. 4.935/2021",
        "pais": "Brasil",
    },
}

AVISO_LEGAL_EXCHANGE_NAO_AUTORIZADA = """
⚠ AVISO LEGAL — EXCHANGE NÃO INTEGRADA AO SISTEMA DOC

Esta exchange não consta na whitelist operacional do DOC (referência BACEN LC 179/2021).
O operador deve verificar autorização e regulamentação vigentes à data.

Caso opere fora desta lista, a responsabilidade por declarações (GCAP, DIRPF)
e recolhimento de tributos é exclusiva do contribuinte — consulte profissional habilitado.

Ref.: IN RFB 1.888/2019 — documentação interna DOC-Module, não é assessoria tributária.
""".strip()


@dataclass
class EntradaDOC:
    """Entrada do diário — imutável após `fechar_posicao` (use estorno com novo registo)."""

    data_abertura: datetime
    ativo: str
    exchange: str
    direcao: str
    entrada_brl: float
    quantidade_ativo: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_registro_utc: str = field(
        default_factory=lambda: datetime.now(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    data_fechamento: Optional[datetime] = None
    saida_brl: Optional[float] = None
    taxas_exchange_brl: float = 0.0
    taxas_rede_brl: float = 0.0
    categoria: str = "ABERTO"
    lucro_bruto_brl: Optional[float] = None
    lucro_liquido_brl: Optional[float] = None
    ir_apurado_brl: Optional[float] = None
    isento: Optional[bool] = None
    codigo_darf: Optional[str] = None
    agente_responsavel: str = ""
    hash_integridade: str = ""
    estorno_de_id: Optional[str] = None
    avisos: list[str] = field(default_factory=list)

    def payload_hash_basico(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp_registro_utc,
            "ativo": self.ativo,
            "exchange": self.exchange,
            "entrada_brl": round(self.entrada_brl, 8),
            "data_abertura": self.data_abertura.isoformat(),
        }

    def gerar_hash(self) -> str:
        payload = json.dumps(self.payload_hash_basico(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def garantir_exchange_autorizada(self) -> None:
        if self.exchange.upper() not in EXCHANGES_AUTORIZADAS:
            msg = AVISO_LEGAL_EXCHANGE_NAO_AUTORIZADA
            self.avisos.append(msg)
            logger.warning("Exchange não listada DOC: %s — aviso registado.", self.exchange)
            logger.info(msg)

    def fechar_posicao(
        self,
        data_fechamento: datetime,
        saida_brl: float,
        *,
        volume_vendido_mes_sw_brl: float,
        taxas_exchange_brl: Optional[float] = None,
        taxas_rede_brl: Optional[float] = None,
    ) -> None:
        """Fecha posição e aplica classificação fiscal determinística."""
        if self.data_fechamento is not None:
            raise RuntimeError("Entrada já fechada; use fluxo de estorno com novo registo.")
        self.data_fechamento = data_fechamento
        self.saida_brl = saida_brl
        if taxas_exchange_brl is not None:
            self.taxas_exchange_brl = taxas_exchange_brl
        if taxas_rede_brl is not None:
            self.taxas_rede_brl = taxas_rede_brl

        bruto = saida_brl - self.entrada_brl
        self.lucro_bruto_brl = round(bruto, 2)
        ded = self.taxas_exchange_brl + self.taxas_rede_brl
        self.lucro_liquido_brl = round(bruto - ded, 2)

        cls = classificar_operacao_fechada(
            self.data_abertura,
            data_fechamento,
            volume_vendido_mes_brl=volume_vendido_mes_sw_brl,
        )
        self.categoria = cls["categoria"]
        self.isento = cls["isencao"]
        self.codigo_darf = cls["codigo_darf"]

        liq = self.lucro_liquido_brl or 0.0
        if self.categoria == "DAY_TRADE" and liq > 0:
            self.ir_apurado_brl = round(liq * float(cls["aliquota"]), 2)
        elif self.categoria == "SWING_TRADE" and liq > 0 and not cls["isencao"]:
            self.ir_apurado_brl = round(liq * float(cls["aliquota"]), 2)
        else:
            self.ir_apurado_brl = 0.0

        self.hash_integridade = self.gerar_hash()


def serializar_entrada(e: EntradaDOC) -> Dict[str, Any]:
    """JSON-friendly."""
    d = asdict(e)
    d["data_abertura"] = e.data_abertura.isoformat()
    if e.data_fechamento:
        d["data_fechamento"] = e.data_fechamento.isoformat()
    return d


def volume_vendido_swing_do_mes(entradas: list[EntradaDOC], ano: int, mes: int) -> float:
    total = 0.0
    for ent in entradas:
        if not ent.data_fechamento:
            continue
        if getattr(ent, "categoria", None) != "SWING_TRADE":
            continue
        if ent.data_fechamento.year != ano or ent.data_fechamento.month != mes:
            continue
        if ent.saida_brl:
            total += ent.saida_brl
    return round(total, 2)


def primeiro_dia_proximo_mes(ano: int, mes: int) -> date:
    if mes == 12:
        return date(ano + 1, 1, 1)
    return date(ano, mes + 1, 1)
