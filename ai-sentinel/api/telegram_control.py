import json
import os
import threading
import time
from typing import Dict, List, Optional

import requests


class TelegramControlService:
    def __init__(self, telegram_bot, private_desk, signal_scanner, copy_trade_service):
        self.telegram_bot = telegram_bot
        self.private_desk = private_desk
        self.signal_scanner = signal_scanner
        self.copy_trade_service = copy_trade_service
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.timeout_seconds = float(os.getenv("TELEGRAM_TIMEOUT_SECONDS", "10"))
        self.poll_timeout_seconds = int(os.getenv("TELEGRAM_POLL_TIMEOUT_SECONDS", "20"))
        self.enabled = os.getenv("TELEGRAM_CONTROL_ENABLED", "false").lower() == "true"
        self.admin_chat_ids = self._parse_env_list("TELEGRAM_ADMIN_CHAT_IDS")
        self.admin_user_ids = self._parse_env_list("TELEGRAM_ADMIN_USER_IDS")
        self._offset = 0
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_error = None
        self._last_seen_chat_id = None
        self._last_seen_user_id = None
        self._last_command = None

    def _parse_env_list(self, env_name: str) -> List[str]:
        raw = os.getenv(env_name, "")
        return [item.strip() for item in raw.split(",") if item.strip()]

    def configured(self) -> bool:
        return bool(self.bot_token and (self.admin_chat_ids or self.admin_user_ids))

    def status(self) -> Dict[str, object]:
        return {
            "enabled": self.enabled,
            "configured": self.configured(),
            "running": self._thread is not None and self._thread.is_alive(),
            "admin_chat_ids": self.admin_chat_ids,
            "admin_user_ids": self.admin_user_ids,
            "last_error": self._last_error,
            "last_seen_chat_id": self._last_seen_chat_id,
            "last_seen_user_id": self._last_seen_user_id,
            "last_command": self._last_command,
        }

    def start(self) -> Dict[str, object]:
        if not self.enabled:
            return {"started": False, "reason": "telegram_control_desabilitado"}
        if not self.configured():
            return {"started": False, "reason": "telegram_control_nao_configurado"}
        if self._thread is not None and self._thread.is_alive():
            return {"started": False, "reason": "telegram_control_ja_ativo"}

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_loop, name="uni-ia-telegram-control", daemon=True)
        self._thread.start()
        return {"started": True}

    def stop(self) -> Dict[str, object]:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        self._thread = None
        return {"stopped": True}

    def _poll_loop(self):
        while not self._stop_event.is_set():
            try:
                updates = self._get_updates()
                for update in updates:
                    self._offset = max(self._offset, update.get("update_id", 0) + 1)
                    self._handle_update(update)
            except Exception as err:
                self._last_error = str(err)
                time.sleep(1)

    def _get_updates(self) -> List[Dict[str, object]]:
        response = requests.get(
            f"https://api.telegram.org/bot{self.bot_token}/getUpdates",
            params={
                "offset": self._offset,
                "timeout": self.poll_timeout_seconds,
                "allowed_updates": json.dumps(["message"]),
            },
            timeout=self.timeout_seconds + self.poll_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram getUpdates recusado: {payload}")
        return payload.get("result", [])

    def _authorized(self, message: Dict[str, object]) -> bool:
        chat_id = str(message.get("chat", {}).get("id", ""))
        user_id = str(message.get("from", {}).get("id", ""))
        if self.admin_chat_ids and chat_id in self.admin_chat_ids:
            return True
        if self.admin_user_ids and user_id in self.admin_user_ids:
            return True
        return False

    def _handle_update(self, update: Dict[str, object]):
        message = update.get("message") or {}
        text = (message.get("text") or "").strip()
        if not text.startswith("/"):
            return

        chat_id = str(message.get("chat", {}).get("id", ""))
        user_id = str(message.get("from", {}).get("id", ""))
        self._last_seen_chat_id = chat_id or None
        self._last_seen_user_id = user_id or None
        self._last_command = text
        if not self._authorized(message):
            self.telegram_bot.send_admin_message(chat_id, "Acesso negado para comandos administrativos.")
            return

        response_text = self._dispatch_command(text)
        self.telegram_bot.send_admin_message(chat_id, response_text)

    def _dispatch_command(self, text: str) -> str:
        parts = text.split()
        command = parts[0].split("@")[0].lower()
        args = parts[1:]

        if command in ["/start", "/help"]:
            return self._help_message()
        if command == "/status":
            return self._status_message()
        if command == "/pending":
            return self._pending_message()
        if command == "/approve":
            return self._approve_message(args)
        if command == "/reject":
            return self._reject_message(args)
        if command == "/cycle":
            result = self.signal_scanner.run_cycle()
            return "\n".join(
                [
                    "*Ciclo executado*",
                    f"Sucesso: {result.get('success')}",
                    f"Ciclos totais: {result.get('cycle_count', 'n/d')}",
                    f"Resultados: {len(result.get('results', []))}",
                ]
            )
        return "Comando desconhecido. Use /help."

    def _help_message(self) -> str:
        lines = [
            "*UNI IA Control Bot*",
            "/status - status da mesa, scanner e copy trade",
            "/pending - lista pendencias de aprovacao",
            "/approve <request_id> - aprova e executa a ordem",
            "/reject <request_id> [motivo] - rejeita a ordem",
            "/cycle - roda um ciclo imediato do scanner",
        ]
        return "\n".join(lines)

    def _status_message(self) -> str:
        desk_status = self.private_desk.status()
        scanner_status = self.signal_scanner.status()
        copytrade_status = self.copy_trade_service.status()
        return "\n".join(
            [
                "*UNI IA Status*",
                f"Mesa: {desk_status['desk']['mode']}",
                f"Aprovacao manual: {desk_status['desk']['manual_approval']}",
                f"Pendencias: {desk_status['pending_count']}",
                f"Scanner ativo: {scanner_status['running']}",
                f"Ativos monitorados: {', '.join(scanner_status['config']['assets']) or 'nenhum'}",
                f"Ultimo ciclo: {scanner_status['last_cycle_completed_at'] or 'nunca'}",
                f"Copy trade: {copytrade_status['enabled']}",
                f"Broker pronto: {copytrade_status['broker_ready']}",
            ]
        )

    def _pending_message(self) -> str:
        pending = self.private_desk.list_pending()
        if not pending:
            return "Nenhuma pendencia na mesa no momento."

        lines = ["*Pendencias da Mesa*"]
        for item in pending[:10]:
            lines.append(
                f"- {item['request_id']} | {item['asset']} | score {item['score']} | status {item['status']}"
            )
        if len(pending) > 10:
            lines.append(f"Total pendente: {len(pending)}")
        return "\n".join(lines)

    def _approve_message(self, args: List[str]) -> str:
        if not args:
            return "Uso: /approve <request_id>"
        request_id = args[0]
        result = self.private_desk.approve(request_id)
        execution = result.get("execution", {})
        payload = execution.get("payload", {})
        return "\n".join(
            [
                "*Aprovacao concluida*",
                f"Request: {request_id}",
                f"Acao: {result.get('action')}",
                f"Ativo: {payload.get('symbol', 'n/d')}",
                f"Direcao: {payload.get('side', 'n/d')}",
            ]
        )

    def _reject_message(self, args: List[str]) -> str:
        if not args:
            return "Uso: /reject <request_id> [motivo]"
        request_id = args[0]
        reason = " ".join(args[1:]).strip() or "rejeitado via Telegram"
        result = self.private_desk.reject(request_id, reason=reason)
        return "\n".join(
            [
                "*Rejeicao concluida*",
                f"Request: {request_id}",
                f"Acao: {result.get('action')}",
                f"Motivo: {result.get('reason')}",
            ]
        )