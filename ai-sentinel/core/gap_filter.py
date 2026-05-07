import httpx
from datetime import date

async def get_ptax_yesterday() -> float:
    """Busca PTAX de venda do dia anterior via API BACEN."""
    today = date.today().strftime("%m-%d-%Y")
    url = (
        f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        f"CotacaoDolarDia(dataCotacao=@dataCotacao)"
        f"?@dataCotacao='{today}'&$format=json&$select=cotacaoVenda"
    )
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=5)
        data = r.json()
        return float(data["value"][0]["cotacaoVenda"])

def gap_exceeds_ptax_threshold(
    open_price: float,
    ptax: float,
    threshold: float = 0.004  # 0,4%
) -> bool:
    """Retorna True se o gap for grande demais em relação à PTAX."""
    deviation = abs(open_price - ptax) / ptax
    return deviation > threshold

def gap_exceeds_atr(
    gap_size: float,
    atr14: float,
    multiplier: float = 1.5
) -> bool:
    """Retorna True se o gap for grande demais em relação ao ATR."""
    return gap_size > (atr14 * multiplier)

async def should_trade_gap(
    open_price: float,
    prev_close: float,
    atr14: float,
    has_macro_event: bool
) -> dict:
    """
    Decisão final: operar ou rejeitar o gap.
    Retorna dict com decisão e motivo.
    """
    gap_size = abs(open_price - prev_close)

    if has_macro_event:
        return {"trade": False, "reason": "Evento macroeconômico no dia"}

    try:
        ptax = await get_ptax_yesterday()
        if gap_exceeds_ptax_threshold(open_price, ptax):
            return {"trade": False, "reason": f"Gap excede 0,4% da PTAX ({ptax:.4f})"}
    except Exception:
        pass  # Se API falhar, não bloqueia por PTAX

    if gap_exceeds_atr(gap_size, atr14):
        return {"trade": False, "reason": f"Gap ({gap_size:.1f}) > 1,5x ATR14 ({atr14:.1f})"}

    return {"trade": True, "reason": "Gap dentro dos parâmetros — operar"}