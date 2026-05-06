import os
import time
from typing import Dict, Optional
import requests
from core.schemas import OpportunityAlert

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

    def _post_message(self, token: str, chat_id: str, message: str):
        last_err = None
        base_url = f"https://api.telegram.org/bot{token}"
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    f"{base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
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
        self._post_message(self.bot_token, chat_id, message)
        
    def dispatch_alert(self, alert: OpportunityAlert, operational_context: Optional[Dict[str, str]] = None):
        """
        Método central do robô UNI IA.
        Decide o destino do sinal baseado nas regras de negócio (Free vs Premium).
        """
        
        self._validate_config()

        # Premium para ativos com USD/EUR/BRL no par.
        premium_assets = ["USD", "EUR", "BRL", "BTC", "ETH", "SOL"]
        normalized_asset = (alert.asset or "").upper()
        is_premium_asset = any(code in normalized_asset for code in premium_assets)
        
        if is_premium_asset:
            self._send_to_premium(alert, operational_context)
        else:
            self._send_to_free(alert, operational_context)
            
    def _format_message(self, alert: OpportunityAlert, is_premium: bool, operational_context: Optional[Dict[str, str]] = None) -> str:
        """Formata o output segundo as boas práticas da plataforma com Markdown"""
        classification_badges = {
            "RISCO": "🔴 RISCO",
            "ATENÇÃO": "🟠 ATENCAO",
            "ATENCAO": "🟠 ATENCAO",
            "OPORTUNIDADE": "🟢 OPORTUNIDADE",
        }
        badge = classification_badges.get(alert.classification, f"⚪ {alert.classification}")
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
        direction_label = direction_badges.get(direction, direction)

        lines = [
            "⚡ *UNI IA Signal Desk*",
            f"Ativo: *{alert.asset}*",
            f"Direcao: *{direction_label}*",
            f"Timeframe: *{timeframe}*",
            f"Modo: *{mode}*",
            f"Status: *{badge}*",
            f"Score: *{alert.score:.1f}/100*",
            f"Operacional: *{operational_status}*",
        ]

        if strategy and strategy.execution_hint:
            lines.append(f"Execucao: {strategy.execution_hint}")

        lines.append("")
        lines.append(f"🧠 *Leitura:* {alert.explanation}")

        if strategy and strategy.reasons:
            lines.append("")
            lines.append("📊 *Confluencias:*")
            for reason in strategy.reasons:
                lines.append(f"- {reason}")

        if is_premium:
            lines.append("")
            lines.append("💎 *Fluxo Premium Ativado*")
        
        if alert.position_reversal_alert:
            lines.append("")
            lines.append(f"🚨 *REVERSAO:* {alert.position_reversal_alert}")

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
