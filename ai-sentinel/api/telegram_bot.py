import os
import time
from typing import Dict
import requests
from ..core.schemas import OpportunityAlert

class UniIATelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.free_bot_token = os.getenv("TELEGRAM_FREE_BOT_TOKEN") or self.bot_token
        self.premium_bot_token = os.getenv("TELEGRAM_PREMIUM_BOT_TOKEN") or self.bot_token
        self.free_channel_id = os.getenv("TELEGRAM_FREE_CHANNEL")
        self.premium_channel_id = os.getenv("TELEGRAM_PREMIUM_CHANNEL")
        self.timeout_seconds = float(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "10"))
        self.max_retries = int(os.getenv("TELEGRAM_MAX_RETRIES", "3"))

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
        
    def dispatch_alert(self, alert: OpportunityAlert):
        """
        Método central do robô UNI IA.
        Decide o destino do sinal baseado nas regras de negócio (Free vs Premium).
        """
        
        self._validate_config()

        # Premium para ativos com USD/EUR/BRL no par.
        premium_assets = ["USD", "EUR", "BRL"]
        normalized_asset = (alert.asset or "").upper()
        is_premium_asset = any(code in normalized_asset for code in premium_assets)
        
        if is_premium_asset:
            self._send_to_premium(alert)
        else:
            self._send_to_free(alert)
            
    def _format_message(self, alert: OpportunityAlert, is_premium: bool) -> str:
        """Formata o output segundo as boas práticas da plataforma com Markdown"""
        if alert.classification == "RISCO":
            badge = "🔴 RISCO"
        elif alert.classification == "ATENÇÃO":
            badge = "🟡 ATENÇÃO"
        else:
            badge = "🟢 OPORTUNIDADE"
        
        msg = f"⚡ *UNI IA Alerta* ⚡\n"
        msg += f"Ativo: *{alert.asset}*\n"
        msg += f"Status: {badge} (Score: {alert.score}/100)\n\n"
        msg += f"🧠 *Insight:* {alert.explanation}\n"
        
        if is_premium:
            msg += f"\n💎 *Exclusivo UNI IA Premium*"
        
        if alert.position_reversal_alert:
            msg += f"\n\n🚨 *ALARME DE POSIÇÃO/REVERSÃO*: {alert.position_reversal_alert} 🚨"
            
        return msg

    def _send_to_free(self, alert: OpportunityAlert):
        """Envia para o canal Free"""
        msg = self._format_message(alert, is_premium=False)
        self._post_message(self.free_bot_token, self.free_channel_id, msg)
        print("Alerta enviado para Telegram [FREE]")
        
    def _send_to_premium(self, alert: OpportunityAlert):
        """Envia para o canal Premium (Dólar/Euro/Real)"""
        msg = self._format_message(alert, is_premium=True)
        self._post_message(self.premium_bot_token, self.premium_channel_id, msg)
        print("Alerta enviado para Telegram [PREMIUM]")
