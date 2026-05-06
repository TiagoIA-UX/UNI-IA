"""Feature Store — Persistencia estruturada de features numericas por signal_id.

Toda analise gera um vetor de features computadas (nao opinadas).
Esse vetor e persistido localmente (JSONL) e, quando disponivel, no Supabase.
O dataset acumulado habilita:
  - Treinamento supervisionado (features -> outcome)
  - Recalibracao de pesos da fusion layer (AEGIS)
  - Audit completo de o que o sistema "viu" em cada decisao
"""

import json
import math
import os
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class FeatureStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._log_path = self._resolve_log_path()
        self._supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").rstrip("/")
        self._service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    def _resolve_log_path(self) -> Path:
        configured = os.getenv("FEATURE_STORE_LOG_PATH", "")
        if configured:
            return Path(configured).expanduser().resolve()
        return (Path(__file__).resolve().parents[1] / "runtime_logs" / "feature_store.jsonl").resolve()

    def _supabase_ready(self) -> bool:
        return bool(self._supabase_url and self._service_role_key)

    def _supabase_headers(self) -> Dict[str, str]:
        return {
            "apikey": self._service_role_key,
            "Authorization": f"Bearer {self._service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

    # ------------------------------------------------------------------
    # Persistencia
    # ------------------------------------------------------------------

    def persist(
        self,
        *,
        signal_id: str,
        asset: str,
        agent_name: str,
        features: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Persiste vetor de features para um signal_id + agent_name."""
        normalized_signal_id = str(signal_id or "").strip()
        normalized_asset = str(asset or "").strip().upper()
        normalized_agent_name = str(agent_name or "").strip()
        if not normalized_signal_id:
            raise RuntimeError("feature_store.signal_id obrigatorio.")
        if not normalized_asset:
            raise RuntimeError("feature_store.asset obrigatorio.")
        if not normalized_agent_name:
            raise RuntimeError("feature_store.agent_name obrigatorio.")
        if not isinstance(features, dict) or not features:
            raise RuntimeError("feature_store.features deve ser objeto nao vazio.")

        payload = {
            "signal_id": normalized_signal_id,
            "asset": normalized_asset,
            "agent_name": normalized_agent_name,
            "features": self._sanitize_for_json(features),
            "metadata": self._sanitize_for_json(metadata or {}),
            "recorded_at": _utcnow_iso(),
            "model_version": os.getenv("UNI_IA_MODEL_VERSION", "v1"),
            "feature_schema_version": 1,
        }

        self._append_local(payload)
        sb = self._persist_supabase(payload)
        return {"success": True, "signal_id": normalized_signal_id, "agent_name": normalized_agent_name, "supabase": sb}

    def _sanitize_for_json(self, value: Any):
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                raise RuntimeError("feature_store recebeu valor numerico nao finito.")
            return value
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return {str(key): self._sanitize_for_json(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._sanitize_for_json(item) for item in value]
        return str(value)

    def _append_local(self, payload: Dict[str, Any]):
        with self._lock:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a", encoding="utf-8") as fp:
                fp.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")

    def _persist_supabase(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self._supabase_ready():
            return {"persisted": False, "reason": "supabase_nao_configurado"}
        try:
            resp = requests.post(
                f"{self._supabase_url}/rest/v1/uni_ia_feature_store",
                headers=self._supabase_headers(),
                json=payload,
                timeout=10,
            )
            if not resp.ok:
                return {"persisted": False, "reason": f"HTTP {resp.status_code}: {resp.text[:200]}"}
            return {"persisted": True}
        except Exception as err:
            return {"persisted": False, "reason": str(err)}

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def _iter_entries(self, limit: int = 10000):
        if not self._log_path.exists():
            return
        with self._log_path.open("r", encoding="utf-8") as fp:
            tail = deque(fp, maxlen=max(int(limit), 1))
        for raw in tail:
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj

    def get_features_for_signal(self, signal_id: str) -> List[Dict[str, Any]]:
        """Retorna todos os vetores de features de um signal_id."""
        return [e for e in self._iter_entries() if e.get("signal_id") == signal_id]

    def get_signal_feature_map(self, signal_id: str) -> Dict[str, Dict[str, Any]]:
        rows = self.get_features_for_signal(signal_id)
        return {
            str(row.get("agent_name")): row
            for row in rows
            if row.get("agent_name")
        }

    def get_recent(
        self,
        *,
        limit: int = 100,
        asset: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        cap = max(min(int(limit), 1000), 1)
        norm_asset = asset.upper().strip() if asset else None
        norm_agent = agent_name.strip() if agent_name else None

        rows: List[Dict[str, Any]] = []
        for item in self._iter_entries(limit=cap * 3):
            if norm_asset and str(item.get("asset", "")).upper() != norm_asset:
                continue
            if norm_agent and str(item.get("agent_name", "")) != norm_agent:
                continue
            rows.append(item)

        rows = rows[-cap:]
        rows.reverse()
        return {"success": True, "count": len(rows), "items": rows}

    def export_dataset(
        self,
        *,
        asset: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 50000,
    ) -> List[Dict[str, Any]]:
        """Exporta dataset para treinamento — flat list com features + metadata."""
        norm_asset = asset.upper().strip() if asset else None
        norm_agent = agent_name.strip() if agent_name else None

        rows: List[Dict[str, Any]] = []
        for item in self._iter_entries(limit=max(int(limit), 100)):
            if norm_asset and str(item.get("asset", "")).upper() != norm_asset:
                continue
            if norm_agent and str(item.get("agent_name", "")) != norm_agent:
                continue
            rows.append(item)
        return rows

    def _flatten_numeric_features(self, value: Any, *, prefix: str = "") -> Dict[str, float]:
        flattened: Dict[str, float] = {}

        if isinstance(value, bool):
            if prefix:
                flattened[prefix] = 1.0 if value else 0.0
            return flattened

        if isinstance(value, (int, float)):
            if prefix and not (isinstance(value, float) and not math.isfinite(value)):
                flattened[prefix] = float(value)
            return flattened

        if isinstance(value, dict):
            for key, item in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else str(key)
                flattened.update(self._flatten_numeric_features(item, prefix=next_prefix))
            return flattened

        if isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                next_prefix = f"{prefix}.{index}" if prefix else str(index)
                flattened.update(self._flatten_numeric_features(item, prefix=next_prefix))
            return flattened

        return flattened

    def export_supervised_dataset(
        self,
        *,
        outcome_tracker,
        asset: Optional[str] = None,
        agent_name: Optional[str] = None,
        strategy: Optional[str] = None,
        result: Optional[str] = None,
        regime_id: Optional[str] = None,
        regime_version: Optional[str] = None,
        limit: int = 50000,
        window_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        feature_rows = self.export_dataset(asset=asset, agent_name=agent_name, limit=limit)
        outcome_rows = outcome_tracker.export_outcomes(
            asset=asset,
            strategy=strategy,
            result=result,
            limit=max(limit * 3, 100),
            window_days=window_days,
        )
        outcome_by_signal = {row.get("signal_id"): row for row in outcome_rows if row.get("signal_id")}

        items: List[Dict[str, Any]] = []
        dropped_without_outcome = 0
        norm_regime_id = str(regime_id or "").strip().lower() or None
        norm_regime_version = str(regime_version or "").strip() or None
        feature_map_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for feature_row in feature_rows:
            signal_id = feature_row.get("signal_id")
            outcome = outcome_by_signal.get(signal_id)
            if not outcome:
                dropped_without_outcome += 1
                continue

            signal_feature_map = feature_map_cache.get(signal_id)
            if signal_feature_map is None:
                signal_feature_map = self.get_signal_feature_map(str(signal_id))
                feature_map_cache[str(signal_id)] = signal_feature_map

            regime_row = signal_feature_map.get("REGIME_ENGINE")
            regime_context = {
                "regime_id": None,
                "regime_label": None,
                "regime_version": None,
                "regime_confidence": None,
            }
            if regime_row:
                regime_features = regime_row.get("features", {})
                regime_context = {
                    "regime_id": regime_features.get("regime_id"),
                    "regime_label": regime_features.get("regime_label"),
                    "regime_version": regime_features.get("regime_version"),
                    "regime_confidence": regime_features.get("regime_confidence"),
                }

            if norm_regime_id and str(regime_context.get("regime_id") or "").strip().lower() != norm_regime_id:
                continue
            if norm_regime_version and str(regime_context.get("regime_version") or "").strip() != norm_regime_version:
                continue

            numeric_features = self._flatten_numeric_features(feature_row.get("features", {}))
            items.append(
                {
                    "signal_id": signal_id,
                    "asset": feature_row.get("asset"),
                    "agent_name": feature_row.get("agent_name"),
                    "recorded_at": feature_row.get("recorded_at"),
                    "model_version": feature_row.get("model_version"),
                    "feature_schema_version": feature_row.get("feature_schema_version"),
                    "features": feature_row.get("features", {}),
                    "numeric_features": numeric_features,
                    "metadata": feature_row.get("metadata", {}),
                    "regime": regime_context,
                    "outcome": {
                        "result": outcome.get("result"),
                        "pnl_percent": outcome.get("pnl_percent"),
                        "direction": outcome.get("direction"),
                        "timeframe": outcome.get("timeframe"),
                        "strategy": outcome.get("strategy"),
                        "closed_at": outcome.get("closed_at"),
                    },
                }
            )

        return {
            "success": True,
            "count": len(items),
            "dropped_without_outcome": dropped_without_outcome,
            "items": items,
        }

    def compute_agent_weight_recommendations(
        self,
        *,
        outcome_tracker,
        asset: Optional[str] = None,
        strategy: Optional[str] = None,
        regime_id: Optional[str] = None,
        regime_version: Optional[str] = None,
        limit: int = 50000,
        window_days: int = 90,
        min_samples: int = 5,
    ) -> Dict[str, Any]:
        dataset = self.export_supervised_dataset(
            outcome_tracker=outcome_tracker,
            asset=asset,
            strategy=strategy,
            regime_id=regime_id,
            regime_version=regime_version,
            limit=limit,
            window_days=window_days,
        )
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for item in dataset["items"]:
            agent = str(item.get("agent_name") or "").strip()
            if not agent:
                continue
            grouped.setdefault(agent, []).append(item)

        stats: Dict[str, Dict[str, Any]] = {}
        raw_scores: Dict[str, float] = {}
        for agent, items in grouped.items():
            pnl_values = [float(entry["outcome"].get("pnl_percent") or 0.0) for entry in items]
            wins = sum(1 for value in pnl_values if value > 0)
            losses = sum(1 for value in pnl_values if value < 0)
            total = len(items)
            avg_pnl = sum(pnl_values) / total if total else 0.0
            win_rate = (wins / total * 100.0) if total else 0.0
            confidence_values = [
                float(entry["numeric_features"].get("emitted_confidence"))
                for entry in items
                if "emitted_confidence" in entry["numeric_features"]
            ]
            avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else None

            performance_floor = max(avg_pnl, 0.0)
            hit_rate_factor = max(win_rate / 100.0, 0.05)
            sample_factor = min(total / max(min_samples, 1), 3.0)
            raw_score = performance_floor * hit_rate_factor * sample_factor

            stats[agent] = {
                "samples": total,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 4),
                "avg_pnl_pct": round(avg_pnl, 6),
                "avg_confidence": round(avg_confidence, 4) if avg_confidence is not None else None,
                "eligible": total >= min_samples,
            }
            if total >= min_samples and raw_score > 0:
                raw_scores[agent] = raw_score

        total_score = sum(raw_scores.values())
        recommended_weights = {
            agent: round(score / total_score, 6)
            for agent, score in raw_scores.items()
        } if total_score > 0 else {}

        return {
            "success": True,
            "window_days": window_days,
            "min_samples": min_samples,
            "dataset_count": dataset["count"],
            "regime_id": regime_id,
            "regime_version": regime_version,
            "agents": stats,
            "weights": recommended_weights,
        }
