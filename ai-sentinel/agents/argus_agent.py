"""ARGUS — Agente de Monitoramento de Posicao.

ARGUS fecha o ciclo. Acompanha trades ativos, detecta deterioracao
estrutural, e registra outcome.

Funcao:
  - Monitorar posicoes abertas
  - Detectar reversao/deterioracao via features do ATLAS
  - Registrar outcome real (win/loss/timeout) no OutcomeTracker
  - Manter registry de posicoes ativas em memoria

ARGUS e o unico agente que ESCREVE no OutcomeTracker.
"""

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.feature_store import FeatureStore
from core.outcome_tracker import OutcomeTracker
from core.schemas import OpportunityAlert
from llm.groq_client import GroqClient
from llm.json_utils import extract_json_object


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ArgusAgent:
    """Agente de Monitoramento de Posicao — ARGUS."""

    def __init__(
        self,
        feature_store: Optional[FeatureStore] = None,
        outcome_tracker: Optional[OutcomeTracker] = None,
    ):
        self.feature_store = feature_store or FeatureStore()
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self._llm: Optional[GroqClient] = None
        self._lock = threading.Lock()
        self._active_positions: Dict[str, Dict[str, Any]] = {}

        self.system_prompt = """Voce e o ARGUS, agente de monitoramento de posicao do Zairyx IA.
Voce recebe dados da posicao aberta e features estruturais atuais.
Sua funcao e avaliar se a posicao deve continuar ou ser encerrada.

Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "action": "hold" ou "close" ou "reduce",
    "urgency": "low" ou "medium" ou "high" ou "critical",
    "reason": "Justificativa objetiva."
}"""

    @property
    def llm(self) -> GroqClient:
        if self._llm is None:
            self._llm = GroqClient()
        return self._llm

    # ------------------------------------------------------------------
    # Position registry
    # ------------------------------------------------------------------

    def register_position(
        self,
        *,
        signal_id: str,
        request_id: Optional[str] = None,
        asset: str,
        direction: str,
        entry_price: float,
        timeframe: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Registra posicao aberta para monitoramento."""
        with self._lock:
            self._active_positions[signal_id] = {
                "signal_id": signal_id,
                "request_id": request_id,
                "asset": (asset or "").upper(),
                "direction": (direction or "").lower(),
                "entry_price": float(entry_price),
                "opened_at": _utcnow_iso(),
                "timeframe": timeframe,
                "strategy": strategy,
            }
        return {"registered": True, "signal_id": signal_id}

    def get_active_positions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._active_positions.values())

    def get_active_position(self, signal_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            position = self._active_positions.get(signal_id)
            return dict(position) if position else None

    # ------------------------------------------------------------------
    # Position evaluation
    # ------------------------------------------------------------------

    def evaluate_position(
        self,
        signal_id: str,
        current_price: float,
        atlas_features: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Avalia se posicao deve ser mantida, reduzida ou fechada."""
        with self._lock:
            position = self._active_positions.get(signal_id)

        if not position:
            return {"error": f"Posicao {signal_id} nao encontrada."}

        entry = position["entry_price"]
        direction = position["direction"]

        # Compute P&L
        if direction == "long":
            pnl_pct = ((current_price - entry) / entry) * 100
        elif direction == "short":
            pnl_pct = ((entry - current_price) / entry) * 100
        else:
            pnl_pct = 0.0

        pnl_pct = round(pnl_pct, 4)

        # Build context for LLM
        context = f"Posicao: {position['asset']} {direction} @ {entry}\n"
        context += f"Preco atual: {current_price}\n"
        context += f"P&L: {pnl_pct}%\n"

        if atlas_features:
            context += "Features estruturais atuais:\n"
            for k, v in atlas_features.items():
                if k == "asset" or v is None:
                    continue
                context += f"  {k}: {v}\n"

        response = self.llm.generate_response(self.system_prompt, context)

        try:
            data = extract_json_object(response)
        except Exception:
            data = {"action": "hold", "urgency": "low", "reason": "Falha na avaliacao."}

        return {
            "signal_id": signal_id,
            "asset": position["asset"],
            "direction": direction,
            "entry_price": entry,
            "current_price": current_price,
            "pnl_pct": pnl_pct,
            "recommendation": data,
        }

    # ------------------------------------------------------------------
    # Close position + record outcome
    # ------------------------------------------------------------------

    def close_position(
        self,
        *,
        signal_id: str,
        exit_price: float,
        result: str,
    ) -> Dict[str, Any]:
        """Fecha posicao e registra outcome."""
        with self._lock:
            position = self._active_positions.pop(signal_id, None)

        if not position:
            return {"error": f"Posicao {signal_id} nao encontrada."}

        entry = position["entry_price"]
        direction = position["direction"]

        if direction == "long":
            pnl_pct = ((exit_price - entry) / entry) * 100
        elif direction == "short":
            pnl_pct = ((entry - exit_price) / entry) * 100
        else:
            pnl_pct = 0.0

        # Calculate holding time
        try:
            opened = datetime.fromisoformat(position["opened_at"].replace("Z", "+00:00"))
            holding_seconds = (datetime.now(timezone.utc) - opened).total_seconds()
        except Exception:
            holding_seconds = None

        # Record outcome
        outcome_result = self.outcome_tracker.record_outcome(
            signal_id=signal_id,
            request_id=position.get("request_id"),
            asset=position["asset"],
            direction=direction,
            entry_price=entry,
            exit_price=exit_price,
            pnl_percent=round(pnl_pct, 6),
            result=result,
            holding_seconds=holding_seconds,
            timeframe=position.get("timeframe"),
            strategy=position.get("strategy"),
        )

        return {
            "closed": True,
            "signal_id": signal_id,
            "pnl_pct": round(pnl_pct, 4),
            "result": result,
            "outcome": outcome_result,
        }

    # ------------------------------------------------------------------
    # Reversal check (legacy compatibility)
    # ------------------------------------------------------------------

    def verify_reversal_risk(self, alert: OpportunityAlert) -> Dict[str, Any]:
        """Verifica risco de reversao para posicoes abertas na direcao contraria."""
        prompt = f"O sistema emitiu o seguinte alerta para {alert.asset}:\n"
        prompt += f"Score: {alert.score}\nClassificacao: {alert.classification}\n"
        prompt += f"Explicacao: {alert.explanation}\n"

        if alert.strategy:
            prompt += f"Direcao: {alert.strategy.direction}\n"

        prompt += "Diga se investidores operando na TENDENCIA CONTRARIA devem receber alerta de REVERSAO."

        reversal_prompt = """Voce e o ARGUS. Avalie se ha risco de reversao.
Sua saida DEVE ser UNICA E EXCLUSIVAMENTE um JSON estrito:
{
    "is_reversal_alert": true ou false,
    "reversal_message": "Mensagem de alerta ou vazio se false."
}"""

        response = self.llm.generate_response(reversal_prompt, prompt)
        try:
            return extract_json_object(response)
        except Exception:
            return {"is_reversal_alert": False, "reversal_message": ""}
