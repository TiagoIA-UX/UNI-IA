"""Reward Model — Combina feedback humano + outcome real para calcular reward.

Para cada sinal registrado, o RewardModel calcula um score de reward
combinando:
  - Feedback humano do FeedbackStore (positivo/negativo)
  - Resultado real do OutcomeTracker (win/loss/breakeven/timeout)

O reward resultante alimenta o WeightOptimizer para recalibrar os
pesos dos agentes no OrchestratorAgent.

Formula:
  reward = alpha * human_score + (1 - alpha) * outcome_score
  onde alpha = REWARD_HUMAN_WEIGHT (default 0.4)
"""

import os
from typing import Any, Dict, List, Optional

OUTCOME_SCORE_MAP = {
    "win": 1.0,
    "loss": -1.0,
    "breakeven": 0.1,
    "timeout": -0.2,
}

HUMAN_SCORE_MAP = {
    "positive": 1.0,
    "negative": -1.0,
}


class RewardModel:
    def __init__(self, feedback_store=None, outcome_tracker=None):
        self.feedback_store = feedback_store
        self.outcome_tracker = outcome_tracker
        self._human_weight = float(os.getenv("REWARD_HUMAN_WEIGHT", "0.4"))
        self._outcome_weight = 1.0 - self._human_weight

    # ------------------------------------------------------------------
    # Calculo de reward por sinal
    # ------------------------------------------------------------------

    def compute_reward(
        self,
        *,
        signal_id: str,
        outcome_result: Optional[str] = None,
        human_feedbacks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Calcula reward consolidado para um sinal.

        outcome_result: win | loss | breakeven | timeout | None
        human_feedbacks: lista de dicts com campo 'rating'
        """
        # Score do outcome real
        outcome_score: Optional[float] = None
        if outcome_result:
            outcome_score = OUTCOME_SCORE_MAP.get(outcome_result.lower().strip())

        # Score do feedback humano (media de todos os feedbacks)
        human_score: Optional[float] = None
        if human_feedbacks:
            scores = [
                HUMAN_SCORE_MAP[fb["rating"]]
                for fb in human_feedbacks
                if fb.get("rating") in HUMAN_SCORE_MAP
            ]
            if scores:
                human_score = sum(scores) / len(scores)

        # Combinacao ponderada
        reward: Optional[float] = None
        if outcome_score is not None and human_score is not None:
            reward = self._human_weight * human_score + self._outcome_weight * outcome_score
        elif outcome_score is not None:
            reward = outcome_score
        elif human_score is not None:
            # Sem outcome ainda: reward mais conservador (50% peso)
            reward = human_score * 0.5

        return {
            "signal_id": signal_id,
            "outcome_result": outcome_result,
            "outcome_score": outcome_score,
            "human_score": human_score,
            "human_feedback_count": len(human_feedbacks) if human_feedbacks else 0,
            "reward": round(reward, 4) if reward is not None else None,
            "human_weight": self._human_weight,
            "outcome_weight": self._outcome_weight,
        }

    # ------------------------------------------------------------------
    # Agregacao por agente
    # ------------------------------------------------------------------

    def compute_agent_stats(
        self,
        feedback_limit: int = 500,
    ) -> Dict[str, Dict[str, Any]]:
        """Computa performance agregada por agente usando feedback disponivel.

        Retorna dict: agent_name -> {avg_reward, positive_rate, sample_count}
        """
        if self.feedback_store is None:
            return {}

        feedback_stats = self.feedback_store.stats(limit=feedback_limit)
        by_agent = feedback_stats.get("by_agent", {})

        agent_stats: Dict[str, Dict[str, Any]] = {}
        for agent_name, counts in by_agent.items():
            pos = counts.get("positive", 0)
            neg = counts.get("negative", 0)
            total = pos + neg
            if total == 0:
                continue
            positive_rate = pos / total
            # Reward medio estimado com base so no feedback humano
            avg_reward = (positive_rate * 2.0 - 1.0) * 0.5  # escala [-0.5, +0.5]
            agent_stats[agent_name] = {
                "positive": pos,
                "negative": neg,
                "total": total,
                "positive_rate": round(positive_rate, 4),
                "avg_reward": round(avg_reward, 4),
            }

        return agent_stats

    def summary(self, feedback_limit: int = 500) -> Dict[str, Any]:
        """Resumo geral do reward model."""
        agent_stats = self.compute_agent_stats(feedback_limit=feedback_limit)
        fb_stats = {}
        if self.feedback_store:
            fb_stats = self.feedback_store.stats(limit=feedback_limit)
        return {
            "feedback_summary": fb_stats,
            "agent_stats": agent_stats,
            "human_weight": self._human_weight,
            "outcome_weight": self._outcome_weight,
        }
