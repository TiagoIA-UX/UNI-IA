import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")


@dataclass(frozen=True)
class GroqCompletion:
    """Resultado de uma chamada bem-sucedida ao Groq (texto + metadados para provenance)."""

    text: str
    model: str
    provider: str = "groq"


class GroqClient:
    def __init__(self):
        # Inicializa o client do Groq buscando a chave GROQ_API_KEY do arquivo .env
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Aviso: GROQ_API_KEY não encontrada no ambiente.")
        timeout_s = float(os.getenv("GROQ_TIMEOUT_SECONDS", "90"))
        max_retries_raw = os.getenv("GROQ_MAX_RETRIES", os.getenv("GROQ_SDK_MAX_RETRIES", "2")).strip()
        try:
            max_retries = int(max_retries_raw)
        except ValueError:
            max_retries = 2
        self.client = Groq(api_key=self.api_key, timeout=timeout_s, max_retries=max_retries)
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.force_json_mode = os.getenv("GROQ_FORCE_JSON_MODE", "true").strip().lower() == "true"

    def complete(self, system_prompt: str, user_prompt: str) -> GroqCompletion:
        """Chama o Groq e devolve texto + modelo (para rastreabilidade)."""
        if not self.api_key:
            raise RuntimeError(
                "Groq indisponível: defina GROQ_API_KEY no ambiente "
                "(por exemplo em .env.local na raiz do repositório e reinicie o processo)."
            )

        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
            }

            if self.force_json_mode:
                payload["response_format"] = {"type": "json_object"}

            completion = self.client.chat.completions.create(**payload)
            content = completion.choices[0].message.content
            if not content:
                raise RuntimeError("Groq devolveu choices[0].message.content vazio.")
            return GroqCompletion(text=content, model=str(self.model), provider="groq")
        except Exception as e:
            err_name = type(e).__name__
            msg = (str(e) or "").strip() or "(sem mensagem)"
            hint = ""
            low = msg.lower()
            if "401" in msg or "unauthorized" in low or "invalid_api_key" in low or "api key" in low:
                hint = " Verifique se GROQ_API_KEY é válida e não foi revogada."
            elif "429" in msg or "rate" in low:
                hint = " Cotação ou limite de taxa Groq excedido; aguarde ou ajuste o modelo."
            elif "timeout" in low or err_name in ("TimeoutError", "ReadTimeout"):
                hint = " Timeout na rede/Groq; tente de novo ou aumente GROQ_TIMEOUT_SECONDS."
            raise RuntimeError(f"Falha ao chamar Groq ({self.model}, {err_name}): {msg}.{hint}") from e

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Gera uma resposta baseada na API do Groq."""
        return self.complete(system_prompt, user_prompt).text
