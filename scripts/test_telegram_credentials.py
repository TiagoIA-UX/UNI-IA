"""
Testa credenciais Telegram definidas em .env.local (raiz do repo).
Não imprime tokens completos — só resultado e @username quando OK.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
ENV_LOCAL = ROOT / ".env.local"


def _mask(s: str | None) -> str:
    if not s:
        return "(vazio)"
    s = s.strip()
    if len(s) <= 12:
        return "***"
    return f"{s[:6]}…{s[-4:]}"


def _looks_like_bot_token(value: str) -> bool:
    return bool(re.match(r"^\d+:[A-Za-z0-9_-]+$", (value or "").strip()))


def _get_me(token: str) -> tuple[bool, str]:
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15)
        j = r.json()
        if j.get("ok"):
            u = j.get("result") or {}
            un = u.get("username") or "?"
            return True, f"OK @{un}"
        return False, f"erro API: {j.get('description', r.text[:120])}"
    except Exception as e:
        return False, str(e)[:200]


def _get_chat(token: str, chat_id: str) -> tuple[bool, str]:
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getChat",
            params={"chat_id": chat_id},
            timeout=15,
        )
        j = r.json()
        if j.get("ok"):
            res = j.get("result") or {}
            title = res.get("title") or res.get("username") or res.get("type") or "?"
            return True, f"OK chat: {title}"
        return False, f"erro API: {j.get('description', r.text[:120])}"
    except Exception as e:
        return False, str(e)[:200]


def main() -> int:
    if not ENV_LOCAL.is_file():
        print("Ficheiro .env.local não encontrado na raiz do repositório.")
        return 1

    # Carrega só variáveis necessárias (sem depender de python-dotenv no script)
    vars_needed = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_FREE_BOT_TOKEN",
        "TELEGRAM_PREMIUM_BOT_TOKEN",
        "TELEGRAM_FREE_CHANNEL",
        "TELEGRAM_PREMIUM_CHANNEL",
    ]
    loaded: dict[str, str] = {}
    for line in ENV_LOCAL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key in vars_needed:
            loaded[key] = val

    print("Boitata - teste Telegram (.env.local)")
    print("-" * 50)

    main_tok = loaded.get("TELEGRAM_BOT_TOKEN", "")
    free_tok = loaded.get("TELEGRAM_FREE_BOT_TOKEN", "")
    prem_tok = loaded.get("TELEGRAM_PREMIUM_BOT_TOKEN", "")
    free_ch = loaded.get("TELEGRAM_FREE_CHANNEL", "")
    prem_ch = loaded.get("TELEGRAM_PREMIUM_CHANNEL", "")

    print(f"TELEGRAM_BOT_TOKEN          {_mask(main_tok)}")
    ok_main, msg_main = _get_me(main_tok) if main_tok else (False, "token ausente")
    print(f"  -> getMe: {msg_main}")

    ok_free_final = ok_main
    ok_prem_final = ok_main

    # Tokens secundários (placeholders falham)
    if free_tok:
        print(f"TELEGRAM_FREE_BOT_TOKEN     {_mask(free_tok)}")
        if "REVOGAR" in free_tok.upper() or "SUBSTITUIR" in free_tok.upper():
            print("  -> getMe: IGNORADO (placeholder - use vazio para herdar TELEGRAM_BOT_TOKEN)")
            ok_free_final = ok_main
        else:
            ok_f, msg_f = _get_me(free_tok)
            ok_free_final = ok_f
            print(f"  -> getMe: {msg_f}")
    else:
        print("TELEGRAM_FREE_BOT_TOKEN     (ausente - codigo usa TELEGRAM_BOT_TOKEN)")

    if prem_tok:
        print(f"TELEGRAM_PREMIUM_BOT_TOKEN  {_mask(prem_tok)}")
        if "REVOGAR" in prem_tok.upper() or "SUBSTITUIR" in prem_tok.upper():
            print("  -> getMe: IGNORADO (placeholder - use vazio para herdar TELEGRAM_BOT_TOKEN)")
            ok_prem_final = ok_main
        else:
            ok_p, msg_p = _get_me(prem_tok)
            ok_prem_final = ok_p
            print(f"  -> getMe: {msg_p}")
    else:
        print("TELEGRAM_PREMIUM_BOT_TOKEN  (ausente - codigo usa TELEGRAM_BOT_TOKEN)")

    print("-" * 50)
    print("Canais (getChat: ID numerico ex. -100..., ou @canal_publico):")
    for label, cid, tok in (
        ("TELEGRAM_FREE_CHANNEL", free_ch, free_tok or main_tok),
        ("TELEGRAM_PREMIUM_CHANNEL", prem_ch, prem_tok or main_tok),
    ):
        print(f"{label} {_mask(cid)}")
        if not cid:
            print("  -> getChat: (vazio)")
            continue
        if _looks_like_bot_token(cid):
            print("  -> AVISO: valor parece TOKEN de bot, nao chat_id. Corrija para ID do canal.")
            ok_t, msg_t = _get_me(cid)
            print(f"  -> getMe com esse valor (se bot): {msg_t}; ainda precisa chat_id real para postar.")
            continue
        ok_c, msg_c = _get_chat(tok, cid)
        print(f"  -> getChat (bot que publica): {msg_c}")

    print("-" * 50)
    if ok_main and ok_free_final and ok_prem_final and not free_ch.strip() and not prem_ch.strip():
        print("Resumo: 3 bots validos. Preencha TELEGRAM_FREE_CHANNEL e TELEGRAM_PREMIUM_CHANNEL (ID ou @canal publico).")
        print("  Ajuda: python scripts/telegram_resolve_channel.py (apos publicar nos canais com o bot admin).")
        return 1
    if ok_main and not _looks_like_bot_token(free_ch) and not _looks_like_bot_token(prem_ch) and free_ch and prem_ch:
        tok_f = free_tok or main_tok
        tok_p = prem_tok or main_tok
        ok_cf, _ = _get_chat(tok_f, free_ch)
        ok_cp, _ = _get_chat(tok_p, prem_ch)
        if ok_cf and ok_cp:
            print("Resumo: bots OK e ambos os chats acessiveis pelos bots que publicam.")
            return 0
    print("Resumo: ajuste tokens ou preencha IDs de canal (ver comentarios no .env.local).")
    return 2 if not ok_main else 1


if __name__ == "__main__":
    sys.exit(main())
