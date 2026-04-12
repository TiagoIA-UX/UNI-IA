import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqClient:
    def __init__(self):
        # Inicializa o client do Groq buscando a chave GROQ_API_KEY do arquivo .env
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("Aviso: GROQ_API_KEY não encontrada no ambiente.")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama3-8b-8192" # Modelo rápido e gratuito ideal para agentes
        
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Gera uma resposta baseada na API do Groq."""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2, # Baixa temperatura para respostas mais analíticas e seguras
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Erro ao comunicar com Groq API: {str(e)}"
