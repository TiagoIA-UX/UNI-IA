
from pydantic import BaseModel
from typing import Any, List, Optional


def model_to_dict(model: Any) -> dict:
    if model is None:
        return {}
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError(f"Objeto nao suportado para serializacao: {type(model)!r}")

class AgentSignal(BaseModel):
    """Sinal individual emitido por um dos agentes base"""
    agent_name: str
    asset: str
    signal_type: str # Ex: bullish, bearish, neutral
    confidence: float # 0 a 100
    summary: str
    raw_data: Optional[str] = None


class StrategyDecision(BaseModel):
    mode: str
    direction: str
    timeframe: str
    confidence: float
    operational_status: str
    reasons: List[str]
    execution_hint: Optional[str] = None
    regime_id: Optional[str] = None
    regime_label: Optional[str] = None
    regime_version: Optional[str] = None
    regime_confidence: Optional[float] = None


class SentinelGovernanceDecision(BaseModel):
    signal_id: str
    regime_id: str
    regime_version: str
    sentinel_decision: str
    sentinel_confidence: float
    block_reason_code: str
    expected_confidence_delta: float
    approved: bool
    reason_codes: List[str]
    risk_flags: List[str]

class AgentFailure(BaseModel):
    """Registo de falha real de um agente. Sem placeholders."""
    agent_name: str
    error_type: str
    error_message: str
    is_critical: bool = False


class OpportunityAlert(BaseModel):
    """Alerta final consolidado pelo OrchestratorAgent"""
    asset: str
    score: float # 0 a 100
    classification: str # OPORTUNIDADE | ATENÇÃO | RISCO
    explanation: str
    sources: List[str]
    position_reversal_alert: Optional[str] = None # Alerta de proteção de posições abertas
    strategy: Optional[StrategyDecision] = None
    governance: Optional[SentinelGovernanceDecision] = None
    chart_timeframe: Optional[str] = None
    agent_failures: List[AgentFailure] = []
    integrity_score: float = 100.0
    fast_path_decision: Optional[str] = None
