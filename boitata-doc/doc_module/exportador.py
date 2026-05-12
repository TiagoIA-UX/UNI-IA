"""Exportações JSON / CSV — layout orientado a auditoria externa."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Iterable, List

from doc_module.diario_operacoes import EntradaDOC, serializar_entrada


def exportar_json_gcap_placeholder(entradas: List[EntradaDOC], caminho: Path) -> None:
    """
    Wrapper JSON UTF-8. O mapeamento exato aos campos do GCAP oficial deve ser revisado por contador
    antes de uso em obrigações acessórias.
    """
    payload = {
        "versao_export": "doc-0.1-placeholder",
        "registros": [serializar_entrada(e) for e in entradas],
        "avisos_integridade": "Validar layout GCAP vigente na RFB antes de importar programa oficial.",
    }
    caminho.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def exportar_csv_contador(entradas: Iterable[EntradaDOC]) -> str:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    w.writerow(
        [
            "data_abertura",
            "data_fechamento",
            "ativo",
            "exchange",
            "entrada_brl",
            "saida_brl",
            "taxas_brl",
            "lucro_liquido_brl",
            "categoria",
            "ir_apurado_brl",
            "codigo_darf",
            "hash_operacao",
        ]
    )
    for e in entradas:
        tx = e.taxas_exchange_brl + e.taxas_rede_brl
        w.writerow(
            [
                e.data_abertura.isoformat(),
                e.data_fechamento.isoformat() if e.data_fechamento else "",
                e.ativo,
                e.exchange,
                f"{e.entrada_brl:.8f}".replace(".", ","),
                f"{(e.saida_brl or 0):.8f}".replace(".", ","),
                f"{tx:.8f}".replace(".", ","),
                f"{(e.lucro_liquido_brl or 0):.8f}".replace(".", ","),
                e.categoria,
                f"{(e.ir_apurado_brl or 0):.8f}".replace(".", ","),
                e.codigo_darf or "",
                e.hash_integridade,
            ]
        )
    return "\ufeff" + buf.getvalue()
