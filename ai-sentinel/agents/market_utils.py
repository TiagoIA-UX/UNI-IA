def resolve_market_ticker(asset: str) -> str:
    normalized = (asset or "").upper().replace("/", "").strip()

    if normalized == "USD":
        return "USDBRL=X"
    if normalized == "EUR":
        return "EURBRL=X"
    if normalized == "BRL":
        return "^BVSP"

    if normalized.endswith("USDT") and len(normalized) > 4:
        return f"{normalized[:-4]}-USD"

    if normalized.endswith("USD") and len(normalized) > 3 and normalized.isalpha():
        crypto_bases = {"BTC", "ETH", "SOL", "XRP", "BNB", "ADA", "DOGE", "AVAX", "LTC", "LINK"}
        base_asset = normalized[:-3]
        if base_asset in crypto_bases:
            return f"{base_asset}-USD"

    if len(normalized) == 6 and normalized.isalpha():
        return f"{normalized}=X"

    if normalized.endswith(".SA") or normalized.endswith("=X") or normalized.startswith("^"):
        return normalized

    return f"{normalized}.SA"