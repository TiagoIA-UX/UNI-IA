"""
Ajudar a descobrir TELEGRAM_FREE_CHANNEL / TELEGRAM_PREMIUM_CHANNEL.

1) Adicione cada bot (Free/Premium) como admin do respetivo canal.
2) Publique uma mensagem de teste no canal (ou encaminhe para o bot).
3) Execute:  python scripts/telegram_resolve_channel.py

Nao imprime tokens completos.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env.local"


def _load_key(name: str) -> str:
    if not ENV.is_file():
        print("Sem .env.local na raiz.")
        sys.exit(1)
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == name:
            return v.strip().strip('"').strip("'")
    return ""


def _get_updates(token: str) -> dict:
    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=50"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode())


def _chats_from_updates(data: dict) -> dict[int, str]:
    out: dict[int, str] = {}
    for u in data.get("result") or []:
        for key in ("message", "channel_post", "edited_message", "edited_channel_post"):
            m = u.get(key)
            if not m:
                continue
            ch = m.get("chat") or {}
            cid = ch.get("id")
            if cid is None:
                continue
            label = (
                ch.get("title")
                or ch.get("username")
                or ch.get("type")
                or str(cid)
            )
            out[int(cid)] = str(label)
    return out


def main() -> int:
    free_tok = _load_key("TELEGRAM_FREE_BOT_TOKEN")
    prem_tok = _load_key("TELEGRAM_PREMIUM_BOT_TOKEN")
    if not free_tok or not prem_tok:
        print("Defina TELEGRAM_FREE_BOT_TOKEN e TELEGRAM_PREMIUM_BOT_TOKEN no .env.local primeiro.")
        return 1

    print("Free bot - chats vistos em getUpdates (ultimos eventos):")
    try:
        jf = _get_updates(free_tok)
        cf = _chats_from_updates(jf)
        if not cf:
            print("  (nenhum). Publique no canal com o bot como admin ou envie /start ao bot.")
        else:
            for cid, title in sorted(cf.items()):
                print(f"  {cid}  ({title})")
    except Exception as e:
        print("  erro:", e)

    print("Premium bot - chats vistos em getUpdates:")
    try:
        jp = _get_updates(prem_tok)
        cp = _chats_from_updates(jp)
        if not cp:
            print("  (nenhum). Publique no canal Premium ou envie mensagem ao bot.")
        else:
            for cid, title in sorted(cp.items()):
                print(f"  {cid}  ({title})")
    except Exception as e:
        print("  erro:", e)

    print("\nCopie o ID numerico (canais costumam ser -100...) para TELEGRAM_FREE_CHANNEL e TELEGRAM_PREMIUM_CHANNEL.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
