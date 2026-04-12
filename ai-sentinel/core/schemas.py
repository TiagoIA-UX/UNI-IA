from pydantic import BaseModel
from typing import List, Optional

class AgentSignal(BaseModel):
    """Sinal individual emitido por um dos agentes base"""
    agent_name: str
    asset: str
    signal_type: str # Ex: bullish, bearish, neutral
    confidence: float # 0 a 100
    summary: str
    raw_data: Optional[str] = None

class OpportunityAlert(BaseModel):
    """Alerta final consolidado pelo OrchestratorAgent"""
    asset: str
    score: float # 0 a 100
    classification: str # OPORTUNIDADE | ATENÇÃO | RISCO
    explanation: str
    sources: List[str]
    position_reversal_alert: Optional[str] = None # Alerta de proteção de posições abertas
