from ..core.schemas import OpportunityAlert
from ..llm.groq_client import GroqClient
import json
import re

class PositionMonitorAgent:
    """Agent responsável por disparar alertas críticos de reversão para quem tem posições abertas."""
    def __init__(self):
        self.llm = GroqClient()
        self.system_prompt = """
        Você é o PositionMonitorAgent, o guardião de risco do Zairyx IA.
        Você olha para um alerta prestes a ser emitido e determina se os usuários que têm posições ABERTAS na direção contrária devem zerar suas posições URGENTEMENTE.
        
        Sua saída DEVE ser ÚNICA E EXCLUSIVAMENTE um JSON estrito no formato:
        {
            "is_reversal_alert": true ou false,
            "reversal_message": "Mensagem de ALERTA DE REVERSÃO, orientando fechamento de posições baseada no risco, ou vazio se false."
        }
        """

    def verify_reversal_risk(self, alert: OpportunityAlert) -> dict:
        prompt = f"O Orchestrator acabou de emitir o seguinte Score de Mercado para {alert.asset}:\n"
        prompt += f"Score: {alert.score}\nClassificação: {alert.classification}\n"
        prompt += f"Explicação: {alert.explanation}\n"
        prompt += "Diga se investidores operando na TENDÊNCIA CONTRÁRIA devem receber um alerta imediato de REVERSÃO para fecharem posição."

        response = self.llm.generate_response(self.system_prompt, prompt)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            return {"is_reversal_alert": False, "reversal_message": ""}
            
        return json.loads(json_match.group(0))