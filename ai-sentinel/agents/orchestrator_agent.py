import json
from ..core.schemas import AgentSignal, OpportunityAlert
from ..llm.groq_client import GroqClient
from typing import List

class OrchestratorAgent:
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = """
        Você é o OrchestratorAgent (AEGIS), um arquiteto PhD de decisão financeira responsável por consolidar sinais de múltiplos agentes de IA.
        Seu objetivo é aplicar pesos lógicos nos sinais recebidos (MacroAgent, TrendsAgent, TechnicalAgent, FundamentalistAgent, NewsAgent, SentimentAgent) e gerar um Alerta de Oportunidade.
        
        Sua saída DEVE ser estritamente APENAS um JSON no formato:
        {
          "asset": "NOME DO ATIVO",
          "score": 0 a 100,
          "classification": "OPORTUNIDADE" ou "ATENÇÃO" ou "RISCO",
          "explanation": "Explicação humana do porque este cenário se configurou.",
          "sources": ["Fonte 1", "Fonte 2"]
        }
        """

    def analyze_signals(self, asset: str, signals: List[AgentSignal]) -> OpportunityAlert:
        """Consolida os sinais dos agentes para gerar um alerta."""
        
        # Converte os sinais em formato de texto para o prompt
        signals_text = "\\n".join([
            f"- Agente {s.agent_name}: {s.signal_type} (Confiança: {s.confidence}%)\\nResumo: {s.summary}" 
            for s in signals
        ])
        
        user_prompt = f"Analise os seguintes sinais para o ativo {asset}:\\n{signals_text}"
        
        response = ""
        try:
            response = self.llm.generate_response(self.system_prompt, user_prompt)
            # Tenta parsear a resposta do LLM para o objeto Pydantic
            # Como pedimos JSON estrito, o parse direto costuma funcionar bem
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response_json = json.loads(json_match.group(0))
                return OpportunityAlert(**response_json)
            else:
                raise ValueError("JSON não encontrado na resposta.")
        except Exception as e:
            return OpportunityAlert(
                asset=asset,
                score=0.0,
                classification="ERRO",
                explanation=f"Falha na orquestração: {str(e)}\nRaw Response: {str(response)[:100]}",
                sources=[]
            )
