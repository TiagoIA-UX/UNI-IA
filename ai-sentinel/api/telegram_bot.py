import os
from typing import Dict
from ..core.schemas import OpportunityAlert

class ZairyxTelegramBot:
    def __init__(self):
        # Aqui conectamos com a API do Telegram (ou disparos HTTP) 
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.free_channel_id = os.getenv("TELEGRAM_FREE_CHANNEL")
        self.premium_channel_id = os.getenv("TELEGRAM_PREMIUM_CHANNEL")
        
    def dispatch_alert(self, alert: OpportunityAlert):
        """
        Método central do robô Zairyx IA.
        Decide o destino do sinal baseado nas regras de negócio (Free vs Premium).
        """
        
        # Filtro estrito: Somente DÓLAR, EURO e REAL vão para o Premium
        premium_assets = ["USD", "EUR", "BRL"]
        
        if alert.asset in premium_assets:
            self._send_to_premium(alert)
        else:
            # Qualquer outro ativo considerado essencial vai para o Free
            self._send_to_free(alert)
            
    def _format_message(self, alert: OpportunityAlert, is_premium: bool) -> str:
        """Formata o Output segundo as boas práticas do Zairyx IA/Cardápio com Markdown"""
        badge = "🔴 RISCO" if alert.classification == "RISCO" else "🟢 OPORTUNIDADE"
        
        msg = f"⚡ *Zairyx IA Alerta* ⚡\n"
        msg += f"Ativo: *{alert.asset}*\n"
        msg += f"Status: {badge} (Score: {alert.score}/100)\n\n"
        msg += f"🧠 *Insight:* {alert.explanation}\n"
        
        if is_premium:
            msg += f"\n💎 *Exclusivo Zairyx Premium*"
        
        if alert.position_reversal_alert:
            msg += f"\n\n🚨 *ALARME DE POSIÇÃO/REVERSÃO*: {alert.position_reversal_alert} 🚨"
            
        return msg

    def _send_to_free(self, alert: OpportunityAlert):
        """Envia para o canal Free"""
        msg = self._format_message(alert, is_premium=False)
        print(f"Enviando para Telegram [FREE]:\n{msg}")
        # Futuro: requisição requests.post(f"https://api.telegram.org/bot{self.bot_token}/sendMessage", ...)
        
    def _send_to_premium(self, alert: OpportunityAlert):
        """Envia para o canal Premium (Dólar/Euro/Real)"""
        msg = self._format_message(alert, is_premium=True)
        print(f"Enviando para Telegram [PREMIUM]:\n{msg}")
        # Futuro: requisição requests.post(...)
