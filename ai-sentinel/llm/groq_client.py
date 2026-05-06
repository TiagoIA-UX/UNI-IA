import os
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")

class GroqClient:
    def __init__(self):
        # Inicializa o client do Groq buscando a chave GROQ_API_KEY do arquivo .env
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Aviso: GROQ_API_KEY não encontrada no ambiente.")
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.force_json_mode = os.getenv("GROQ_FORCE_JSON_MODE", "true").strip().lower() == "true"
        
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Gera uma resposta baseada na API do Groq."""
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY ausente no ambiente.")

        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                # Baixa temperatura para respostas mais analíticas e seguras.
                "temperature": 0.2,
            }

            if self.force_json_mode:
                payload["response_format"] = {"type": "json_object"}

            completion = self.client.chat.completions.create(**payload)
            content = completion.choices[0].message.content
            if not content:
                raise RuntimeError("Resposta vazia da Groq API.")
            return content
        except Exception as e:
            raise RuntimeError(f"Falha ao comunicar com Groq API: {str(e)}") from e
