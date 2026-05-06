from typing import List, Optional

from core.schemas import AgentSignal, OpportunityAlert
from core.weight_optimizer import WeightOptimizer
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object

# Instancia compartilhada do otimizador (carregada uma vez do disco)
_weight_optimizer: Optional[WeightOptimizer] = None


def _get_weight_optimizer() -> WeightOptimizer:
    global _weight_optimizer
    if _weight_optimizer is None:
        _weight_optimizer = WeightOptimizer()
    return _weight_optimizer


class OrchestratorAgent:
    def __init__(self):
        self.llm = GroqClient()
        self._base_system_prompt = """
        Você é o OrchestratorAgent, um arquiteto PhD de decisão financeira responsável por consolidar sinais de múltiplos agentes de IA.
        Seu objetivo é aplicar os pesos calibrados de cada agente (informados abaixo) nos sinais recebidos e gerar um Alerta de Oportunidade.
        Agentes com peso maior devem influenciar mais o score final.

        Sua saída DEVE ser estritamente APENAS um JSON no formato:
        {
          "asset": "NOME DO ATIVO",
          "score": 0 a 100,
          "classification": "OPORTUNIDADE" ou "ATENÇÃO" ou "RISCO",
          "explanation": "Explicação humana do porque este cenário se configurou.",
          "sources": ["Fonte 1", "Fonte 2"]
        }
        """

    def _build_system_prompt(self, signals: List[AgentSignal]) -> str:
        """Constroi prompt com pesos atuais dos agentes envolvidos."""
        optimizer = _get_weight_optimizer()
        weights = optimizer.get_weights()

        # Filtra apenas agentes presentes nos sinais recebidos
        involved_agents = {s.agent_name for s in signals}
        weight_lines = []
        for agent_name in sorted(involved_agents):
            w = weights.get(agent_name, 1.0)
            weight_lines.append(f"  - {agent_name}: peso {w:.2f}")

        if weight_lines:
            weights_block = "Pesos calibrados por aprendizado de feedback humano:\n" + "\n".join(weight_lines)
        else:
            weights_block = ""

        return self._base_system_prompt.strip() + (f"\n\n{weights_block}" if weights_block else "")

    def analyze_signals(self, asset: str, signals: List[AgentSignal]) -> OpportunityAlert:
        """Consolida os sinais dos agentes para gerar um alerta."""
        response = ""
        system_prompt = self._build_system_prompt(signals)
        signals_text = "\n".join(
            f"- Agente {signal.agent_name}: {signal.signal_type} (Confiança: {signal.confidence}%)\nResumo: {signal.summary}"
            for signal in signals
        )
        user_prompt = f"Analise os seguintes sinais para o ativo {asset}:\n{signals_text}"

        try:
            response = self.llm.generate_response(system_prompt, user_prompt)
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
