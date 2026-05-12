from datetime import datetime

from doc_module.apuracao_fiscal import LIMIAR_ISENCAO_SWING, apurar_mes, classificar_operacao_fechada
from doc_module.diario_operacoes import EXCHANGES_AUTORIZADAS, EntradaDOC
from doc_module.despesas import calcular_despesa_energia


def test_day_trade_mesmo_dia():
    d0 = datetime(2026, 5, 10, 10, 0, 0)
    d1 = datetime(2026, 5, 10, 22, 0, 0)
    c = classificar_operacao_fechada(d0, d1, volume_vendido_mes_brl=999_999)
    assert c["categoria"] == "DAY_TRADE"
    assert c["aliquota"] == 0.20


def test_swing_isento_volume_abaixo_limite():
    d0 = datetime(2026, 5, 1, 10, 0, 0)
    d1 = datetime(2026, 5, 5, 10, 0, 0)
    c = classificar_operacao_fechada(d0, d1, volume_vendido_mes_brl=LIMIAR_ISENCAO_SWING)
    assert c["categoria"] == "SWING_TRADE"
    assert c["isencao"] is True


def test_swing_tributavel_acima_limite():
    d0 = datetime(2026, 5, 1, 10, 0, 0)
    d1 = datetime(2026, 5, 5, 10, 0, 0)
    c = classificar_operacao_fechada(d0, d1, volume_vendido_mes_brl=LIMIAR_ISENCAO_SWING + 1)
    assert c["isencao"] is False
    assert c["aliquota"] == 0.15


def test_entrada_hash_idempotente():
    e = EntradaDOC(
        data_abertura=datetime(2026, 5, 1, 8, 0, 0),
        ativo="BTC-BRL",
        exchange="MERCADO_BITCOIN",
        direcao="LONG",
        entrada_brl=100_000.0,
        quantidade_ativo=0.25,
    )
    h1 = e.gerar_hash()
    h2 = e.gerar_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_exchange_desconhecida_insere_aviso():
    e = EntradaDOC(
        data_abertura=datetime(2026, 5, 1, 8, 0, 0),
        ativo="BTC-BRL",
        exchange="BINANCE_INTL",
        direcao="LONG",
        entrada_brl=1.0,
        quantidade_ativo=0.00001,
    )
    e.garantir_exchange_autorizada()
    assert len(e.avisos) == 1


def test_apurar_mes_carry_prejuizo_dt():
    class _E:
        def __init__(self, cat, liq, saida=0.0):
            self.categoria = cat
            self.lucro_liquido_brl = liq
            self.saida_brl = saida

    ent = [_E("DAY_TRADE", -500.0), _E("DAY_TRADE", 800.0)]
    r = apurar_mes(ent, carry_forward_dt=0.0, carry_forward_st=0.0)
    assert r["ir_day_trade"] == round(300 * 0.20, 2)


def test_energia():
    r = calcular_despesa_energia(400.0, 18.0, 30, 0.85)
    assert r["custo_brl"] > 0


def test_whitelist_nao_vazia():
    assert "MERCADO_BITCOIN" in EXCHANGES_AUTORIZADAS
