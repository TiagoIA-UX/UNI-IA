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
        # O "CÉREBRO" DO MENTOR: Aqui definimos a personalidade amigável
        self._base_system_prompt = """
        Você é o Mentor e Estrategista-Chefe da UNI IA. Sua missão é traduzir dados complexos de múltiplos robôs de análise para um investidor iniciante e leigo.
        
        DIRETRIZES DE COMUNICAÇÃO:
        1. Fale como um mentor humano, cortês e direto ao ponto.
        2. No campo "explanation", NUNCA use termos como RSI, MACD ou Médias Móveis. 
        3. Traduza a técnica para frases como: "O mercado está com muita força", "Momento de cautela e proteção", "Oportunidade clara de lucro rápido".
        4. Sempre dê um conselho dividido: um para quem quer rapidez (Scalper) e outro para quem tem paciência (Swing Trader).
        5. Seja honesto sobre os riscos.

        Sua saída DEVE ser estritamente APENAS um JSON no formato:
        {
          "asset": "NOME DO ATIVO",
          "score": 0 a 100,
          "classification": "OPORTUNIDADE" ou "ATENÇÃO" ou "RISCO",
          "explanation": "Sua explicação humana, simples e mentoria aqui.",
          "sources": ["Fontes analisadas pela IA"]
        }
        """

    def _build_system_prompt(self, signals: List[AgentSignal]) -> str:
        """Constrói o prompt final unindo a base com os pesos dos agentes."""
        optimizer = _get_weight_optimizer()
        weights = optimizer.get_weights()

        involved_agents = {s.agent_name for s in signals}
        weight_lines = []
        for agent_name in sorted(involved_agents):
            w = weights.get(agent_name, 1.0)
            weight_lines.append(f"  - {agent_name}: importância {w:.2f}")

        if weight_lines:
            weights_block = "Nível de importância atual dos seus ajudantes de IA:\n" + "\n".join(weight_lines)
        else:
            weights_block = ""

        return self._base_system_prompt.strip() + (f"\n\n{weights_block}" if weights_block else "")

    def analyze_signals(self, asset: str, signals: List[AgentSignal]) -> OpportunityAlert:
        """Consolida os sinais dos agentes e entrega a mentoria para o usuário."""
        response = ""
        system_prompt = self._build_system_prompt(signals)
        
        # Traduzindo os sinais internos para a IA entender o contexto antes de falar com o humano
        signals_text = "\n".join(
            f"- Agente {signal.agent_name}: {signal.signal_type} (Confiança: {signal.confidence}%)\nResumo Técnico: {signal.summary}"
            for signal in signals
        )
        
        user_prompt = f"Mentor, analise os sinais para {asset} e me dê sua visão humana:\n{signals_text}"

        try:
            response = self.llm.generate_response(system_prompt, user_prompt)
            response_json = extract_json_object(response)
            
            # Garante que o retorno siga o formato esperado pelo seu Front-end
            return OpportunityAlert(**response_json)
            
        except Exception as error:
            # Em caso de erro, avisa o usuário de forma clara
            return OpportunityAlert(
                asset=asset,
                score=0.0,
                classification="ATENÇÃO",
                explanation=f"Estou com dificuldade de conexão agora, mas estou de olho. Erro: {str(error)}",
                sources=[],
            )