from typing import List

from core.schemas import AgentSignal, OpportunityAlert
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object


class OrchestratorAgent:
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = """
        Você é o OrchestratorAgent, um arquiteto PhD de decisão financeira responsável por consolidar sinais de múltiplos agentes de IA.
        Seu objetivo é aplicar pesos lógicos nos sinais recebidos (News, Sentiment, Macro, Trends) e gerar um Alerta de Oportunidade.

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

        signals_text = "\n".join(
            f"- Agente {signal.agent_name}: {signal.signal_type} (Confiança: {signal.confidence}%)\nResumo: {signal.summary}"
            for signal in signals
        )
        user_prompt = f"Analise os seguintes sinais para o ativo {asset}:\n{signals_text}"

        try:
            response = self.llm.generate_response(self.system_prompt, user_prompt)
            response_json = extract_json_object(response)
            return OpportunityAlert(**response_json)
        except Exception as error:
            return OpportunityAlert(
                asset=asset,
                score=0.0,
                classification="ERRO",
                explanation=f"Falha na orquestração: {str(error)}\nRaw Response: {response[:100]}",
                sources=[],
            )
