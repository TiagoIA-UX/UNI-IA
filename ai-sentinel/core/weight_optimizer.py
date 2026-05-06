"""Weight Optimizer — Calibracao dinamica dos pesos dos agentes.

Mantém um vetor de pesos por agente que é atualizado via EMA
(Exponential Moving Average) baseado no reward acumulado do RewardModel.

Os pesos afetam diretamente o prompt do OrchestratorAgent, que os usa
para ponderar a importancia de cada agente ao consolidar sinais.

Persistencia: JSON local (weights nao precisam de historico completo).
Limites de seguranca:
  - Peso minimo: 0.2 (nenhum agente e completamente ignorado)
  - Peso maximo: 2.5 (nenhum agente domina sozinho)
  - EMA alpha: 0.1 (atualizacoes suaves, evita oscilacoes bruscas)
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# Pesos iniciais neutros para todos os agentes conhecidos
DEFAULT_WEIGHTS: Dict[str, float] = {
    "NewsAgent": 1.0,
    "SentimentAgent": 1.0,
    "MacroAgent": 1.0,
    "TechnicalAgent": 1.0,
    "TrendsAgent": 1.0,
    "OrionAgent": 1.0,
    "ArgusAgent": 1.0,
    "AtlasAgent": 1.0,
    "FundamentalistAgent": 1.0,
}

WEIGHT_MIN = 0.2
WEIGHT_MAX = 2.5
EMA_ALPHA = float(os.getenv("WEIGHT_OPTIMIZER_EMA_ALPHA", "0.1"))


class WeightOptimizer:
    def __init__(self):
        self._lock = threading.Lock()
        self._weights_path = self._resolve_weights_path()
        self._weights: Dict[str, float] = {}
        self._updated_at: Optional[str] = None
        self._load()

    def _resolve_weights_path(self) -> Path:
        configured = os.getenv("WEIGHT_OPTIMIZER_PATH", "")
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "agent_weights.json").resolve()

    # ------------------------------------------------------------------
    # Carregamento e persistencia
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Carrega pesos do disco; inicializa com defaults se nao existir."""
        with self._lock:
            if self._weights_path.exists():
                try:
                    raw = json.loads(self._weights_path.read_text(encoding="utf-8"))
                    self._weights = raw.get("weights", {})
                    self._updated_at = raw.get("updated_at")
                except (json.JSONDecodeError, KeyError):
                    self._weights = {}
            # Garantir que todos os agentes default existam
            for agent, default_w in DEFAULT_WEIGHTS.items():
                self._weights.setdefault(agent, default_w)

    def _save(self) -> None:
        """Persiste pesos no disco (chamado com lock ja adquirido)."""
        self._weights_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "weights": self._weights,
            "updated_at": self._updated_at,
        }
        self._weights_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def get_weights(self) -> Dict[str, float]:
        """Retorna copia dos pesos atuais."""
        with self._lock:
            return dict(self._weights)

    def get_weight(self, agent_name: str) -> float:
        """Retorna peso de um agente especifico (default 1.0 se desconhecido)."""
        with self._lock:
            return self._weights.get(agent_name, 1.0)

    def update_from_agent_stats(
        self,
        agent_stats: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Atualiza pesos via EMA baseado nos stats do RewardModel.

        agent_stats: {agent_name: {avg_reward: float, ...}}
        Retorna dict com pesos antes e depois da atualizacao.
        """
        if not agent_stats:
            return {"updated": 0, "weights": self.get_weights()}

        with self._lock:
            before = dict(self._weights)
            updated_count = 0

            for agent_name, stats in agent_stats.items():
                avg_reward = stats.get("avg_reward")
                if avg_reward is None:
                    continue
                sample_count = stats.get("total", 0)
                # Exigir minimo de amostras para atualizar peso
                if sample_count < int(os.getenv("WEIGHT_OPTIMIZER_MIN_SAMPLES", "3")):
                    continue

                current = self._weights.get(agent_name, 1.0)
                # Novo peso = reward normalizado para escala [WEIGHT_MIN, WEIGHT_MAX]
                # avg_reward esta em [-0.5, +0.5], mapeamos para fator em [0.5, 1.5]
                target = 1.0 + avg_reward * 2.0  # [-0.5,+0.5] -> [0.0, 2.0]
                target = max(WEIGHT_MIN, min(WEIGHT_MAX, target))
                # EMA: suaviza a transicao
                new_weight = current + EMA_ALPHA * (target - current)
                new_weight = max(WEIGHT_MIN, min(WEIGHT_MAX, new_weight))
                self._weights[agent_name] = round(new_weight, 4)
                updated_count += 1

            self._updated_at = _utcnow_iso()
            self._save()

        return {
            "updated": updated_count,
            "updated_at": self._updated_at,
            "before": before,
            "after": dict(self._weights),
        }

    def reset_weights(self) -> Dict[str, float]:
        """Reseta todos os pesos para o valor neutro (1.0)."""
        with self._lock:
            self._weights = dict(DEFAULT_WEIGHTS)
            self._updated_at = _utcnow_iso()
            self._save()
        return dict(self._weights)

    def status(self) -> Dict[str, Any]:
        """Status completo do otimizador."""
        weights = self.get_weights()
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        return {
            "weights": weights,
            "top_agents": [{"agent": k, "weight": v} for k, v in sorted_weights[:3]],
            "bottom_agents": [{"agent": k, "weight": v} for k, v in sorted_weights[-3:]],
            "updated_at": self._updated_at,
            "ema_alpha": EMA_ALPHA,
            "weight_min": WEIGHT_MIN,
            "weight_max": WEIGHT_MAX,
        }
