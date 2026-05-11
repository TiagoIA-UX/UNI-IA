import uuid
from typing import Any, Dict, Optional

from core.contract_validation import normalize_classification, validate_agent_signal, validate_opportunity_alert
from core.feature_store import FeatureStore
from core.outcome_tracker import OutcomeTracker
from core.regime_engine import RegimeEngine
from core.schemas import OpportunityAlert, SentinelGovernanceDecision
from core.sentinel_decision_store import SentinelDecisionStore
from core.system_state import SystemStateManager


class AnalysisService:
    """Pipeline de analise com arquitetura nomeada:
    ATLAS -> ORION -> (legacy agents) -> AEGIS -> SENTINEL -> ARGUS
    """

    def __init__(
        self,
        feature_store: Optional[FeatureStore] = None,
        outcome_tracker: Optional[OutcomeTracker] = None,
        system_state: Optional[SystemStateManager] = None,
        sentinel_store: Optional[SentinelDecisionStore] = None,
    ):
        self.feature_store = feature_store or FeatureStore()
        self.outcome_tracker = outcome_tracker or OutcomeTracker()
        self.regime_engine = RegimeEngine()
        self.system_state = system_state
        self.sentinel_store = sentinel_store or SentinelDecisionStore()
        from agents.argus_agent import ArgusAgent

        self.argus = ArgusAgent(feature_store=self.feature_store, outcome_tracker=self.outcome_tracker)

    def _apply_sentinel_governance(self, alert: OpportunityAlert, governance_result: dict) -> OpportunityAlert:
        alert.governance = SentinelGovernanceDecision(
            signal_id=str(governance_result["signal_id"]),
            regime_id=str(governance_result["regime_id"]),
            regime_version=str(governance_result["regime_version"]),
            sentinel_decision=str(governance_result["sentinel_decision"]),
            sentinel_confidence=float(governance_result["sentinel_confidence"]),
            block_reason_code=str(governance_result["block_reason_code"]),
            expected_confidence_delta=float(governance_result["expected_confidence_delta"]),
            approved=bool(governance_result["approved"]),
            reason_codes=list(governance_result.get("reason_codes", [])),
            risk_flags=list(governance_result.get("risk_flags", [])),
        )

        if alert.strategy:
            alert.strategy.operational_status = (
                "sentinel_blocked" if alert.governance.sentinel_decision == "block"
                else "sentinel_downgraded" if alert.governance.sentinel_decision == "downgrade"
                else alert.strategy.operational_status
            )
            alert.strategy.confidence = max(
                0.0,
                min(100.0, float(alert.strategy.confidence) + float(alert.governance.expected_confidence_delta)),
            )
        if alert.governance.sentinel_decision == "downgrade":
            alert.score = max(0.0, min(100.0, float(alert.score) + float(alert.governance.expected_confidence_delta)))
        return alert

    def analyze(self, asset: str, signal_id: Optional[str] = None, chart_timeframe: Optional[str] = None) -> OpportunityAlert:
        from agents.atlas_agent import AtlasAgent
        from agents.macro_agent import MacroAgent
        from agents.news_agent import NewsAgent
        from agents.orion_agent import OrionAgent
        from agents.sentiment_agent import SentimentAgent
        from agents.trends_agent import TrendsAgent
        from agents.fundamentalist_agent import FundamentalistAgent
        from agents.aegis_agent import AegisAgent
        from agents.sentinel_agent import SentinelAgent

        sid = signal_id or str(uuid.uuid4())

        print(f"[{asset}] INICIANDO VARREDURA ZAIRYX IA (signal_id={sid[:8]}...)")

        agents_data = []

        macro = validate_agent_signal(
            MacroAgent(feature_store=self.feature_store).analyze_macro_context(asset, signal_id=sid),
            expected_asset=asset,
        )
        agents_data.append(macro)
        print(f"[{asset}] Macro OK: {macro.signal_type} (conf={macro.confidence})")

        # === ATLAS — Agente Estrutural Tecnico ===
        atlas = AtlasAgent(feature_store=self.feature_store)
        atlas_signal = validate_agent_signal(
            atlas.analyze(asset, signal_id=sid, chart_timeframe=chart_timeframe),
            expected_asset=asset,
        )
        agents_data.append(atlas_signal)
        print(f"[{asset}] ATLAS OK: {atlas_signal.signal_type} (conf={atlas_signal.confidence})")

        # === ORION — Agente Cognitivo de Noticias ===
        orion = OrionAgent(feature_store=self.feature_store)
        orion_signal = validate_agent_signal(orion.analyze(asset, signal_id=sid), expected_asset=asset)
        agents_data.append(orion_signal)
        print(f"[{asset}] ORION OK: {orion_signal.signal_type} (conf={orion_signal.confidence})")

        news_signal = validate_agent_signal(
            NewsAgent(feature_store=self.feature_store).analyze_news(asset, signal_id=sid),
            expected_asset=asset,
        )
        agents_data.append(news_signal)
        print(f"[{asset}] News OK: {news_signal.signal_type} (conf={news_signal.confidence})")

        initial_feature_map = self.feature_store.get_signal_feature_map(sid)
        macro_features = initial_feature_map.get("MacroAgent", {}).get("features", {})
        atlas_features = initial_feature_map.get("ATLAS", {}).get("features", {})
        orion_features = initial_feature_map.get("ORION", {}).get("features", {})
        news_features = initial_feature_map.get("NewsAgent", {}).get("features", {})

        regime_context = self.regime_engine.classify(
            asset=asset,
            macro_signal=macro,
            atlas_signal=atlas_signal,
            orion_signal=orion_signal,
            news_signal=news_signal,
            macro_features=macro_features,
            atlas_features=atlas_features,
            orion_features=orion_features,
            news_features=news_features,
        )
        self.feature_store.persist(
            signal_id=sid,
            asset=asset,
            agent_name="REGIME_ENGINE",
            features={
                **regime_context.regime_features,
                "regime_id": regime_context.regime_id,
                "regime_label": regime_context.regime_label,
                "regime_version": regime_context.regime_version,
                "regime_confidence": regime_context.regime_confidence,
            },
            metadata={
                "summary": regime_context.regime_label,
            },
        )
        print(
            f"[{asset}] REGIME OK: {regime_context.regime_id} "
            f"(conf={regime_context.regime_confidence})"
        )

        # === Legacy agents (complementares) ===
        trends = validate_agent_signal(
            TrendsAgent(feature_store=self.feature_store).analyze_trends(asset, signal_id=sid),
            expected_asset=asset,
        )
        agents_data.append(trends)
        print(f"[{asset}] Trends OK: {trends.signal_type}")

        fund = validate_agent_signal(
            FundamentalistAgent(feature_store=self.feature_store).analyze_fundamentals(asset, signal_id=sid),
            expected_asset=asset,
        )
        agents_data.append(fund)
        print(f"[{asset}] Fundamentalist OK: {fund.signal_type}")

        if not news_signal.raw_data:
            raise RuntimeError("NewsAgent nao retornou manchetes brutas para o SentimentAgent.")

        senti = validate_agent_signal(
            SentimentAgent(feature_store=self.feature_store).analyze_sentiment(asset, news_signal.raw_data, signal_id=sid),
            expected_asset=asset,
        )
        agents_data.append(senti)
        print(f"[{asset}] Sentiment OK: {senti.signal_type}")

        # === AEGIS — Fusao Ponderada ===
        aegis = AegisAgent(feature_store=self.feature_store, outcome_tracker=self.outcome_tracker)
        alert = validate_opportunity_alert(
            aegis.fuse(asset, agents_data, signal_id=sid, regime_context=regime_context, chart_timeframe=chart_timeframe),
            expected_asset=asset,
        )
        print(f"[{asset}] AEGIS FUSION: score={alert.score} class={alert.classification} dir={alert.strategy.direction if alert.strategy else 'N/A'}")

        sentinel = SentinelAgent(
            system_state=self.system_state,
            feature_store=self.feature_store,
            outcome_tracker=self.outcome_tracker,
            sentinel_store=self.sentinel_store,
        )
        sentinel_result = sentinel.evaluate(alert, signal_id=sid, regime_context=regime_context)
        sentinel_result["signal_id"] = sid
        alert = self._apply_sentinel_governance(alert, sentinel_result)
        alert = validate_opportunity_alert(alert, expected_asset=asset)
        print(
            f"[{asset}] SENTINEL: {alert.governance.sentinel_decision} "
            f"reason={alert.governance.block_reason_code}"
        )

        if not alert.governance.approved:
            print(f"[{asset}] PIPELINE BLOQUEADO PELO SENTINEL (signal_id={sid[:8]}...)")
            return alert

        # === ARGUS — Reversal Check ===
        guard = self.argus.verify_reversal_risk(alert)
        if guard.get("is_reversal_alert"):
            alert.position_reversal_alert = guard.get("reversal_message")
            print(f"[{asset}] ARGUS: ALERTA DE REVERSAO ATIVADO")

        print(f"[{asset}] PIPELINE COMPLETO (signal_id={sid[:8]}...)")
        return alert

    def _entry_price_for_signal(self, signal_id: str) -> Optional[float]:
        fm = self.feature_store.get_signal_feature_map(signal_id)
        atlas = fm.get("ATLAS", {}).get("features", {}) or {}
        for key in ("user_chart_tf_last_close", "price_last"):
            v = atlas.get(key)
            if v is None:
                continue
            try:
                p = float(v)
                if p > 0:
                    return p
            except (TypeError, ValueError):
                continue
        return None

    def register_argus_after_desk_pipeline(
        self,
        alert: OpportunityAlert,
        desk_result: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Apos a mesa (execucao real ou paper opcional), regista posicao ARGUS com timeframe canónico."""
        import os

        from core.chart_timeframes import normalize_chart_timeframe

        if not alert.governance or not alert.governance.approved:
            return None
        if normalize_classification(alert.classification) != "OPORTUNIDADE":
            return None
        if not alert.strategy or alert.strategy.direction not in ("long", "short"):
            return None

        sid = alert.governance.signal_id
        action = desk_result.get("action")
        entry: Optional[float] = None

        if action == "executed":
            ex = desk_result.get("execution") or {}
            br = ex.get("broker_response") or {}
            pb = br.get("price_brl")
            if isinstance(pb, (int, float)) and float(pb) > 0:
                entry = float(pb)
            if entry is None:
                entry = self._entry_price_for_signal(sid)
        elif action == "paper_logged":
            if os.getenv("ARGUS_REGISTER_PAPER_OPPORTUNITY", "false").lower() != "true":
                return None
            entry = self._entry_price_for_signal(sid)
        else:
            return None

        if not entry or entry <= 0:
            return None

        tf_raw = alert.chart_timeframe or (alert.strategy.timeframe if alert.strategy else None)
        tf = normalize_chart_timeframe(tf_raw) if tf_raw else None
        strat = alert.strategy.mode if alert.strategy else None
        req_id = desk_result.get("request_id")

        return self.argus.register_position(
            signal_id=sid,
            request_id=req_id,
            asset=alert.asset,
            direction=alert.strategy.direction,
            entry_price=entry,
            timeframe=tf,
            strategy=strat,
        )

    def register_argus_after_manual_execution(
        self,
        *,
        asset: str,
        side: str,
        entry_price: float,
        chart_timeframe: Optional[str] = None,
        strategy_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ordem manual executada no broker: novo signal_id e registo ARGUS com TF da UI."""
        from core.chart_timeframes import normalize_chart_timeframe

        side_u = (side or "").strip().upper()
        if side_u in ("COMPRA", "BUY"):
            direction = "long"
        elif side_u in ("VENDA", "SELL"):
            direction = "short"
        else:
            raise ValueError("side invalido para ARGUS")

        tf = normalize_chart_timeframe(chart_timeframe) if chart_timeframe else None
        sid = str(uuid.uuid4())
        mode = strategy_mode or "manual_desk"
        return self.argus.register_position(
            signal_id=sid,
            request_id=None,
            asset=(asset or "").upper(),
            direction=direction,
            entry_price=float(entry_price),
            timeframe=tf,
            strategy=mode,
        )
