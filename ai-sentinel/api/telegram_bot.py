import html
import os
import time
from typing import Any, Dict, Optional, Tuple

import requests
from core.contract_validation import normalize_classification
from core.schemas import OpportunityAlert


def _env_truthy(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None or str(raw).strip() == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def normalize_telegram_dispatch_result(raw: Any) -> Dict[str, Any]:
    """Compat com `dispatch_alert` dict ou valor legado bool."""
    if isinstance(raw, dict):
        return {
            "success": bool(raw.get("success", True)),
            "dispatched": bool(raw.get("dispatched")),
            "gate_reason": raw.get("gate_reason"),
            "error": raw.get("error"),
        }
    return {"success": True, "dispatched": bool(raw), "gate_reason": None, "error": None}


class UniIATelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.free_bot_token = os.getenv("TELEGRAM_FREE_BOT_TOKEN") or self.bot_token
        self.premium_bot_token = os.getenv("TELEGRAM_PREMIUM_BOT_TOKEN") or self.bot_token
        self.free_channel_id = os.getenv("TELEGRAM_FREE_CHANNEL")
        self.premium_channel_id = os.getenv("TELEGRAM_PREMIUM_CHANNEL")
        self.timeout_seconds = float(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "10"))
        self.max_retries = int(os.getenv("TELEGRAM_MAX_RETRIES", "3"))

    def configured(self) -> bool:
        return bool(
            self.free_bot_token
            and self.premium_bot_token
            and self.free_channel_id
            and self.premium_channel_id
        )

    def _validate_config(self):
        missing = []
        if not self.free_bot_token:
            missing.append("TELEGRAM_FREE_BOT_TOKEN/TELEGRAM_BOT_TOKEN")
        if not self.premium_bot_token:
            missing.append("TELEGRAM_PREMIUM_BOT_TOKEN/TELEGRAM_BOT_TOKEN")
        if not self.free_channel_id:
            missing.append("TELEGRAM_FREE_CHANNEL")
        if not self.premium_channel_id:
            missing.append("TELEGRAM_PREMIUM_CHANNEL")
        if missing:
            raise RuntimeError(f"Telegram nao configurado. Variaveis faltando: {', '.join(missing)}")

    def _should_dispatch_public_alert(self, alert: OpportunityAlert) -> Tuple[bool, str]:
        """Cadeia de seguranca antes de publicar em canais Free/Premium.

        Boas praticas operacionais / governanca de capital:
        - Nao divulgar como sinal publico quando o SENTINEL nao aprovou.
        - Restringir classificacoes (por defeito so OPORTUNIDADE).
        - Nao divulgar direcao FLAT como convite a operar.
        - Exigir integridade minima do pipeline (muitos agentes falhados = leitura fraca).
        - Quando o motor rapido bloqueia (fast_path=block), nao misturar com "dica de trade"
          em canais amplos — isso reduz sinais contraditorios (ATLAS/FAST_PATH vs AEGIS).
        """
        if _env_truthy("TELEGRAM_PUBLIC_DISPATCH_REQUIRE_APPROVED", True):
            if alert.governance is None:
                return False, "governance_ausente"
            if not alert.governance.approved:
                return False, "sentinel_nao_aprovou"

        if _env_truthy("TELEGRAM_REQUIRE_FAST_PATH_NOT_BLOCK", True):
            fp = (alert.fast_path_decision or "").strip().lower()
            if fp == "block":
                return False, "fast_path_block"

        min_score = float(os.getenv("TELEGRAM_MIN_SCORE", "75"))
        if float(alert.score) < min_score:
            return False, "score_abaixo_minimo_telegram"

        min_integ = float(os.getenv("TELEGRAM_MIN_INTEGRITY_SCORE", "60"))
        if float(getattr(alert, "integrity_score", 100.0) or 0.0) < min_integ:
            return False, "integridade_abaixo_minimo"

        allow_raw = (os.getenv("TELEGRAM_PUBLIC_CLASSIFICATIONS") or "OPORTUNIDADE").strip()
        allowed: set = set()
        for part in allow_raw.split(","):
            p = part.strip()
            if not p:
                continue
            try:
                allowed.add(normalize_classification(p))
            except Exception:
                continue
        if not allowed:
            allowed = {"OPORTUNIDADE"}
        try:
            cls_norm = normalize_classification(alert.classification)
        except Exception:
            return False, "classificacao_invalida"
        if cls_norm not in allowed:
            return False, f"classificacao_{cls_norm}_fora_da_lista"

        if _env_truthy("TELEGRAM_SKIP_FLAT_DIRECTION", True):
            if not alert.strategy:
                return False, "estrategia_ausente"
            if str(alert.strategy.direction or "").lower() == "flat":
                return False, "direcao_flat"

        return True, "ok"

    @staticmethod
    def _infer_quote_bucket(asset: str) -> str:
        """Moeda de cotacao inferida pelo sufixo do par (ex.: BTCBRL -> BRL, BTCUSDT -> USDT)."""
        u = (asset or "").upper().replace("-", "").replace("/", "")
        if u.endswith("BRL"):
            return "BRL"
        for suf in ("USDT", "USDC", "BUSD", "DAI"):
            if u.endswith(suf):
                return "STABLE_USD"
        if u.endswith("USD"):
            return "USD"
        if u.endswith("EUR"):
            return "EUR"
        if u.endswith("GBP"):
            return "GBP"
        return "UNKNOWN"

    def _route_premium_by_quote(self, alert: OpportunityAlert) -> bool:
        """Premium = cotacao internacional (USD/stable/EUR/GBP); Free = BRL e desconhecido (por defeito)."""
        bucket = self._infer_quote_bucket(alert.asset or "")
        if bucket == "BRL":
            return False
        if bucket in {"USD", "STABLE_USD", "EUR", "GBP"}:
            return True
        return _env_truthy("TELEGRAM_UNKNOWN_QUOTE_TO_PREMIUM", False)

    def _post_message(self, token: str, chat_id: str, message: str, parse_mode: Optional[str] = "HTML"):
        last_err = None
        base_url = f"https://api.telegram.org/bot{token}"
        for attempt in range(1, self.max_retries + 1):
            try:
                payload = {
                    "chat_id": chat_id,
                    "text": message,
                    "disable_web_page_preview": True,
                }
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                response = requests.post(
                    f"{base_url}/sendMessage",
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                if response.ok:
                    return
                detail = response.text[:300]
                raise RuntimeError(f"Telegram HTTP {response.status_code}: {detail}")
            except Exception as err:
                last_err = err
                if attempt < self.max_retries:
                    time.sleep(attempt * 0.4)
        raise RuntimeError(f"Falha no envio Telegram apos {self.max_retries} tentativas: {last_err}")

    def send_admin_message(self, chat_id: str, message: str):
        if not self.bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN nao configurado para comandos administrativos.")
        self._post_message(self.bot_token, chat_id, message, parse_mode=None)

    def dispatch_alert(
        self, alert: OpportunityAlert, operational_context: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Envia para Free ou Premium conforme a moeda de cotacao do par.

        Returns:
            success: False apenas em falha de rede/API Telegram.
            dispatched: True se uma mensagem foi enviada.
            gate_reason: preenchido quando gates suprimiram o envio (nao e falha operacional).
        """
        self._validate_config()

        ok, reason = self._should_dispatch_public_alert(alert)
        if not ok:
            print(f"Telegram: envio publico ignorado ({reason}) — {alert.asset}")
            return {"success": True, "dispatched": False, "gate_reason": reason, "error": None}

        try:
            if self._route_premium_by_quote(alert):
                self._send_to_premium(alert, operational_context)
            else:
                self._send_to_free(alert, operational_context)
            return {"success": True, "dispatched": True, "gate_reason": None, "error": None}
        except Exception as exc:
            return {"success": False, "dispatched": False, "gate_reason": None, "error": str(exc)}

    def _format_message(self, alert: OpportunityAlert, is_premium: bool, operational_context: Optional[Dict[str, str]] = None) -> str:
        """Formata o alerta em HTML (parse_mode HTML) com escape de conteudo dinamico."""
        def esc(s: object) -> str:
            return html.escape(str(s) if s is not None else "", quote=False)

        classification_badges = {
            "RISCO": "🔴 RISCO",
            "ATENÇÃO": "🟠 ATENCAO",
            "ATENCAO": "🟠 ATENCAO",
            "OPORTUNIDADE": "🟢 OPORTUNIDADE",
        }
        raw_class = alert.classification or ""
        badge = classification_badges.get(raw_class, f"⚪ {esc(raw_class)}")
        strategy = alert.strategy
        direction = strategy.direction.upper() if strategy and strategy.direction else "FLAT"
        timeframe = strategy.timeframe if strategy and strategy.timeframe else "N/D"
        mode = strategy.mode.upper() if strategy and strategy.mode else "ANALYTICS"
        operational_status = "monitorando"
        if operational_context and operational_context.get("operational_status"):
            operational_status = operational_context["operational_status"]
        elif strategy and strategy.operational_status:
            operational_status = strategy.operational_status

        direction_badges = {
            "LONG": "🟢 LONG",
            "SHORT": "🔴 SHORT",
            "FLAT": "⚪ FLAT",
        }
        direction_label = direction_badges.get(direction, esc(direction))

        lines = [
            "⚡ <b>UNI IA Signal Desk</b>",
            f"Ativo: <b>{esc(alert.asset)}</b>",
            f"Direcao: <b>{esc(direction_label)}</b>",
            f"Timeframe: <b>{esc(timeframe)}</b>",
            f"Modo: <b>{esc(mode)}</b>",
            f"Status: <b>{esc(badge)}</b>",
            f"Score: <b>{alert.score:.1f}/100</b>",
            f"Operacional: <b>{esc(operational_status)}</b>",
        ]

        if strategy and strategy.execution_hint:
            lines.append(f"Execucao: {esc(strategy.execution_hint)}")

        lines.append("")
        expl = alert.explanation or ""
        lines.append(f"🧠 <b>Leitura:</b> {esc(expl)}")

        if strategy and strategy.reasons:
            lines.append("")
            lines.append("📊 <b>Confluencias:</b>")
            for reason in strategy.reasons:
                lines.append(f"- {esc(reason)}")

        if is_premium:
            lines.append("")
            lines.append("💎 <b>Fluxo Premium Ativado</b>")

        if alert.position_reversal_alert:
            lines.append("")
            lines.append(f"🚨 <b>REVERSAO:</b> {esc(alert.position_reversal_alert)}")

        lines.append("")
        lines.append(
            "⚖️ <i>Conteudo educativo/operacional interno; nao e recomendacao personalizada, "
            "ordem ou promessa de resultado. Criptoativos: risco de perda total do capital.</i>"
        )

        return "\n".join(lines)

    def _send_to_free(self, alert: OpportunityAlert, operational_context: Optional[Dict[str, str]] = None):
        """Envia para o canal Free"""
        msg = self._format_message(alert, is_premium=False, operational_context=operational_context)
        self._post_message(self.free_bot_token, self.free_channel_id, msg)
        print("Alerta enviado para Telegram [FREE]")
        
    def _send_to_premium(self, alert: OpportunityAlert, operational_context: Optional[Dict[str, str]] = None):
        """Envia para o canal Premium (Dólar/Euro/Real)"""
        msg = self._format_message(alert, is_premium=True, operational_context=operational_context)
        self._post_message(self.premium_bot_token, self.premium_channel_id, msg)
        print("Alerta enviado para Telegram [PREMIUM]")
