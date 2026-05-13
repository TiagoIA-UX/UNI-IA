import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core.chart_timeframes import normalize_chart_timeframe, timeframe_strategy_legenda
from core.contract_validation import normalize_classification, validate_agent_signal, validate_opportunity_alert
from core.execution_engine_fast import evaluate_fast_path
from core.feature_store import FeatureStore
from core.outcome_tracker import OutcomeTracker
from core.regime_engine import RegimeEngine
from core.schemas import AgentFailure, AgentSignal, OpportunityAlert, SentinelGovernanceDecision, StrategyDecision
from core.sentinel_decision_store import SentinelDecisionStore
from core.system_state import SystemStateManager


# Agentes obrigatorios para AEGIS poder fundir com seguranca.
_CRITICAL_AGENTS = frozenset({"ATLAS"})

# Mapeamento de funcoes -> nome canonico do AgentSignal.
_AGENT_LABELS = {
    "macro": "MacroAgent",
    "atlas": "ATLAS",
    "orion": "ORION",
    "news": "NewsAgent",
    "trends": "TrendsAgent",
    "fundamentalist": "FundamentalistAgent",
    "sentiment": "SentimentAgent",
}

_FAST_SCALP_TFS = frozenset({"1m", "2m", "5m", "15m"})


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
        # Ultimo snapshot por (ativo, timeframe) para GET /api/signal/summary (evita 2º pipeline completo).
        self._plataforma_signal_by_key: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def plataforma_signal_cache_key(asset: str, chart_tf: Optional[str]) -> str:
        a = (asset or "").strip().upper().replace("-", "")
        t = (chart_tf or "").strip().lower() or "default"
        return f"{a}|{t}"

    def record_plataforma_signal(
        self,
        asset: str,
        chart_tf: Optional[str],
        snapshot: Dict[str, Any],
    ) -> None:
        key = self.plataforma_signal_cache_key(asset, chart_tf)
        self._plataforma_signal_by_key[key] = {
            "recorded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            **snapshot,
        }

    def get_plataforma_signal(self, asset: str, chart_tf: Optional[str]) -> Optional[Dict[str, Any]]:
        return self._plataforma_signal_by_key.get(self.plataforma_signal_cache_key(asset, chart_tf))

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

    def _run_agent_safely(
        self,
        *,
        label: str,
        runner,
    ) -> Tuple[Optional[AgentSignal], Optional[AgentFailure]]:
        """Executa um agente capturando excecao. Nao inventa dados; reporta falha real."""
        agent_name = _AGENT_LABELS[label]
        try:
            signal = runner()
            return signal, None
        except Exception as exc:
            failure = AgentFailure(
                agent_name=agent_name,
                error_type=type(exc).__name__,
                error_message=str(exc)[:512],
                is_critical=agent_name in _CRITICAL_AGENTS,
            )
            return None, failure

    @staticmethod
    def _is_fast_scalp_timeframe(tf_norm: Optional[str]) -> bool:
        return tf_norm in _FAST_SCALP_TFS

    @staticmethod
    def _signal_type_from_fast_decision(decision: str, confidence: float) -> str:
        if decision == "long":
            return "STRONG BUY" if confidence >= 80.0 else "BUY"
        if decision == "short":
            return "STRONG SELL" if confidence >= 80.0 else "SELL"
        return "NEUTRAL"

    @staticmethod
    def _direction_from_fast_decision(decision: str) -> str:
        if decision == "long":
            return "long"
        if decision == "short":
            return "short"
        return "flat"

    @staticmethod
    def _classification_from_fast_decision(decision: str, confidence: float) -> str:
        if decision in {"block", "flat"}:
            return "RISCO"
        if confidence >= 75.0:
            return "OPORTUNIDADE"
        if confidence >= 60.0:
            return "ATENCAO"
        return "RISCO"

    @staticmethod
    def _trend_signal_from_atlas_features(asset: str, features: Dict[str, Any]) -> AgentSignal:
        vol_ratio = features.get("user_chart_tf_volume_ratio")
        if vol_ratio is None:
            vol_ratio = features.get("volume_ratio")
        try:
            ratio = float(vol_ratio)
        except (TypeError, ValueError):
            ratio = 0.0

        if ratio >= 1.5:
            signal_type = "FOMO"
            confidence = min(95.0, 60.0 + (ratio - 1.0) * 20.0)
            summary = f"Volume relativo forte no timeframe do gatilho (ratio={ratio:.2f})."
        elif ratio > 0 and ratio <= 0.5:
            signal_type = "FEAR"
            confidence = 65.0
            summary = f"Volume fino para scalping (ratio={ratio:.2f}); reduzir agressividade."
        else:
            signal_type = "IGNORE"
            confidence = 50.0
            summary = f"Volume sem anomalia decisiva para scalping (ratio={ratio:.2f})."

        return AgentSignal(
            agent_name="TrendsAgent",
            asset=asset,
            signal_type=signal_type,
            confidence=round(float(confidence), 2),
            summary=summary,
            raw_data=f"volume_ratio={ratio:.6f}",
        )

    def _analyze_fast_scalp(
        self,
        *,
        asset: str,
        sid: str,
        tf_norm: Optional[str],
        legenda: str,
    ) -> OpportunityAlert:
        from agents.atlas_agent import AtlasAgent
        from agents.sentinel_agent import SentinelAgent

        atlas = AtlasAgent(feature_store=self.feature_store)
        atlas_features = atlas.compute_features(asset, chart_timeframe=tf_norm)
        fast_path = evaluate_fast_path(atlas_features=atlas_features, chart_timeframe=tf_norm)
        confidence = float(fast_path.get("confidence_pct") or 0.0)
        decision = str(fast_path.get("decision") or "block")
        direction = self._direction_from_fast_decision(decision)
        signal_type = self._signal_type_from_fast_decision(decision, confidence)

        atlas_summary = (
            f"FAST_SCALP {tf_norm}: {decision} "
            f"conf={confidence:.2f}; {', '.join(fast_path.get('reasons', [])[:4])}"
        )
        atlas_signal = AgentSignal(
            agent_name="ATLAS",
            asset=asset,
            signal_type=signal_type,
            confidence=confidence,
            summary=atlas_summary,
            raw_data=str(fast_path.get("features_used", {})),
        )
        trends = self._trend_signal_from_atlas_features(asset, atlas_features)

        self.feature_store.persist(
            signal_id=sid,
            asset=asset,
            agent_name="ATLAS",
            features={**atlas_features, "emitted_confidence": confidence},
            metadata={
                "signal_type": atlas_signal.signal_type,
                "summary": atlas_signal.summary,
                "mode": "FAST_SCALP",
                "strategy_legenda": legenda,
            },
        )
        try:
            trends_ratio = float(str(trends.raw_data or "").split("=", 1)[1])
        except (IndexError, TypeError, ValueError):
            trends_ratio = None

        self.feature_store.persist(
            signal_id=sid,
            asset=asset,
            agent_name="TrendsAgent",
            features={
                "volume_ratio": trends_ratio,
                "emitted_confidence": float(trends.confidence),
            },
            metadata={
                "signal_type": trends.signal_type,
                "summary": trends.summary,
                "mode": "FAST_SCALP",
            },
        )
        self.feature_store.persist(
            signal_id=sid,
            asset=asset,
            agent_name="EXECUTION_ENGINE_FAST",
            features={
                "decision": decision,
                "confidence_pct": confidence,
                "strategy_family": fast_path.get("strategy_family"),
                **{f"feat_{k}": v for k, v in fast_path.get("features_used", {}).items()},
            },
            metadata={
                "mode": "FAST_SCALP",
                "reasons": fast_path.get("reasons", []),
                "missing": fast_path.get("missing", []),
                "weights_template": fast_path.get("weights_template", {}),
            },
        )

        regime_context = self.regime_engine.classify(
            asset=asset,
            macro_signal=None,
            atlas_signal=atlas_signal,
            orion_signal=None,
            news_signal=None,
            atlas_features=atlas_features,
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
            metadata={"summary": regime_context.regime_label, "mode": "FAST_SCALP"},
        )

        classification = self._classification_from_fast_decision(decision, confidence)
        reasons = list(fast_path.get("reasons", []))[:6]
        reasons.append(trends.summary)
        if decision == "block":
            reasons.append("Entrada bloqueada pelo fast path antes de chamar agentes lentos.")

        strategy = StrategyDecision(
            mode="fast_scalp",
            direction=direction,
            timeframe=tf_norm or "n/a",
            confidence=confidence,
            operational_status="fast_scalp_ready" if direction != "flat" else "fast_scalp_blocked",
            reasons=reasons,
            execution_hint="gatilho rapido; noticias/macro nao entram no caminho critico",
            regime_id=regime_context.regime_id,
            regime_label=regime_context.regime_label,
            regime_version=regime_context.regime_version,
            regime_confidence=regime_context.regime_confidence,
        )
        alert = OpportunityAlert(
            asset=asset,
            score=confidence,
            classification=classification,
            explanation=f"FAST_SCALP {tf_norm}: decisao {decision} com score {confidence:.2f}.",
            sources=["ATLAS", "TrendsAgent", "EXECUTION_ENGINE_FAST"],
            strategy=strategy,
            chart_timeframe=tf_norm,
            agent_failures=[],
            integrity_score=100.0,
            fast_path_decision=decision,
        )

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
            f"[{asset}] FAST_SCALP: decision={decision} score={alert.score} "
            f"sentinel={alert.governance.sentinel_decision if alert.governance else 'none'}"
        )
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

        tf_norm = normalize_chart_timeframe(chart_timeframe) if chart_timeframe else None
        legenda = timeframe_strategy_legenda(tf_norm)

        print(f"[{asset}] INICIANDO VARREDURA ZAIRYX IA (signal_id={sid[:8]}...)")

        if self._is_fast_scalp_timeframe(tf_norm):
            return self._analyze_fast_scalp(asset=asset, sid=sid, tf_norm=tf_norm, legenda=legenda)

        agents_data: List[AgentSignal] = []
        agent_failures: List[AgentFailure] = []

        def _run_macro():
            return validate_agent_signal(
                MacroAgent(feature_store=self.feature_store).analyze_macro_context(
                    asset, signal_id=sid, strategy_legenda=legenda
                ),
                expected_asset=asset,
            )

        def _run_atlas():
            return validate_agent_signal(
                AtlasAgent(feature_store=self.feature_store).analyze(
                    asset, signal_id=sid, chart_timeframe=tf_norm, strategy_legenda=legenda
                ),
                expected_asset=asset,
            )

        def _run_orion():
            return validate_agent_signal(
                OrionAgent(feature_store=self.feature_store).analyze(asset, signal_id=sid, strategy_legenda=legenda),
                expected_asset=asset,
            )

        def _run_news():
            return validate_agent_signal(
                NewsAgent(feature_store=self.feature_store).analyze_news(asset, signal_id=sid, strategy_legenda=legenda),
                expected_asset=asset,
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            fut_macro = pool.submit(self._run_agent_safely, label="macro", runner=_run_macro)
            fut_atlas = pool.submit(self._run_agent_safely, label="atlas", runner=_run_atlas)
            fut_orion = pool.submit(self._run_agent_safely, label="orion", runner=_run_orion)
            fut_news = pool.submit(self._run_agent_safely, label="news", runner=_run_news)
            macro, f_macro = fut_macro.result()
            atlas_signal, f_atlas = fut_atlas.result()
            orion_signal, f_orion = fut_orion.result()
            news_signal, f_news = fut_news.result()

        for sig in (macro, atlas_signal, orion_signal, news_signal):
            if sig is not None:
                agents_data.append(sig)

        for failure in (f_macro, f_atlas, f_orion, f_news):
            if failure is not None:
                agent_failures.append(failure)
                print(f"[{asset}] AGENT FAIL {failure.agent_name}: {failure.error_type}: {failure.error_message}")

        for sig in (macro, atlas_signal, orion_signal, news_signal):
            if sig is not None:
                print(f"[{asset}] {sig.agent_name} OK: {sig.signal_type} (conf={sig.confidence})")

        critical_failed = [f for f in agent_failures if f.is_critical]
        if critical_failed:
            failure_summary = "; ".join(f"{f.agent_name}={f.error_type}" for f in critical_failed)
            return self._build_blocked_alert(
                asset=asset,
                sid=sid,
                tf_norm=tf_norm,
                reason=f"agent_critico_falhou:{failure_summary}",
                agent_failures=agent_failures,
                integrity_score=self._compute_integrity_score(agents_data, agent_failures),
            )

        initial_feature_map = self.feature_store.get_signal_feature_map(sid)
        macro_features = initial_feature_map.get("MacroAgent", {}).get("features", {})
        atlas_features = initial_feature_map.get("ATLAS", {}).get("features", {})
        orion_features = initial_feature_map.get("ORION", {}).get("features", {})
        news_features = initial_feature_map.get("NewsAgent", {}).get("features", {})

        fast_path = evaluate_fast_path(atlas_features=atlas_features, chart_timeframe=tf_norm)
        print(
            f"[{asset}] FAST_PATH decision={fast_path['decision']} "
            f"conf={fast_path['confidence_pct']} family={fast_path.get('strategy_family')}"
        )
        self.feature_store.persist(
            signal_id=sid,
            asset=asset,
            agent_name="EXECUTION_ENGINE_FAST",
            features={
                "decision": fast_path["decision"],
                "confidence_pct": fast_path["confidence_pct"],
                "strategy_family": fast_path.get("strategy_family"),
                **{f"feat_{k}": v for k, v in fast_path.get("features_used", {}).items()},
            },
            metadata={
                "reasons": fast_path.get("reasons", []),
                "missing": fast_path.get("missing", []),
                "weights_template": fast_path.get("weights_template", {}),
            },
        )

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

        def _run_trends():
            return validate_agent_signal(
                TrendsAgent(feature_store=self.feature_store).analyze_trends(
                    asset, signal_id=sid, strategy_legenda=legenda
                ),
                expected_asset=asset,
            )

        def _run_fund():
            return validate_agent_signal(
                FundamentalistAgent(feature_store=self.feature_store).analyze_fundamentals(
                    asset, signal_id=sid, strategy_legenda=legenda
                ),
                expected_asset=asset,
            )

        trends, f_trends = self._run_agent_safely(label="trends", runner=_run_trends)
        if trends is not None:
            agents_data.append(trends)
            print(f"[{asset}] Trends OK: {trends.signal_type}")
        if f_trends is not None:
            agent_failures.append(f_trends)
            print(f"[{asset}] AGENT FAIL {f_trends.agent_name}: {f_trends.error_type}: {f_trends.error_message}")

        fund, f_fund = self._run_agent_safely(label="fundamentalist", runner=_run_fund)
        if fund is not None:
            agents_data.append(fund)
            print(f"[{asset}] Fundamentalist OK: {fund.signal_type}")
        if f_fund is not None:
            agent_failures.append(f_fund)
            print(f"[{asset}] AGENT FAIL {f_fund.agent_name}: {f_fund.error_type}: {f_fund.error_message}")

        if news_signal is not None and news_signal.raw_data:
            def _run_senti():
                return validate_agent_signal(
                    SentimentAgent(feature_store=self.feature_store).analyze_sentiment(
                        asset, news_signal.raw_data, signal_id=sid, strategy_legenda=legenda
                    ),
                    expected_asset=asset,
                )

            senti, f_senti = self._run_agent_safely(label="sentiment", runner=_run_senti)
            if senti is not None:
                agents_data.append(senti)
                print(f"[{asset}] Sentiment OK: {senti.signal_type}")
            if f_senti is not None:
                agent_failures.append(f_senti)
                print(f"[{asset}] AGENT FAIL {f_senti.agent_name}: {f_senti.error_type}: {f_senti.error_message}")
        else:
            agent_failures.append(
                AgentFailure(
                    agent_name="SentimentAgent",
                    error_type="MissingUpstream",
                    error_message="NewsAgent indisponivel: sem manchetes para alimentar Sentiment.",
                    is_critical=False,
                )
            )

        integrity_score = self._compute_integrity_score(agents_data, agent_failures)

        # === AEGIS — Fusao Ponderada ===
        aegis = AegisAgent(feature_store=self.feature_store, outcome_tracker=self.outcome_tracker)
        alert = validate_opportunity_alert(
            aegis.fuse(asset, agents_data, signal_id=sid, regime_context=regime_context, chart_timeframe=tf_norm),
            expected_asset=asset,
        )

        # Ajuste de score por integridade (sem inflar: penaliza proporcional aos agentes que falharam).
        if integrity_score < 100.0 and float(alert.score) > 0:
            penalty = (100.0 - integrity_score) * 0.5  # ate 50pp de corte se cair toda integridade
            alert.score = max(0.0, min(100.0, round(float(alert.score) - penalty, 4)))
            if alert.strategy:
                alert.strategy.confidence = max(0.0, min(99.0, alert.strategy.confidence - penalty))

        alert.agent_failures = list(agent_failures)
        alert.integrity_score = float(integrity_score)
        alert.fast_path_decision = fast_path["decision"]

        print(
            f"[{asset}] AEGIS FUSION: score={alert.score} class={alert.classification} "
            f"dir={alert.strategy.direction if alert.strategy else 'N/A'} integrity={integrity_score}"
        )

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

    def _compute_integrity_score(
        self,
        agents_data: List[AgentSignal],
        agent_failures: List[AgentFailure],
    ) -> float:
        """Percentual de agentes esperados que retornaram dados reais (0-100)."""
        expected = len(_AGENT_LABELS)
        ok = len(agents_data)
        if expected <= 0:
            return 100.0
        return round(max(0.0, min(100.0, (ok / expected) * 100.0)), 4)

    def _build_blocked_alert(
        self,
        *,
        asset: str,
        sid: str,
        tf_norm: Optional[str],
        reason: str,
        agent_failures: List[AgentFailure],
        integrity_score: float,
    ) -> OpportunityAlert:
        """Constroi alerta bloqueado quando agente critico falhou. Sem fallback inflado."""
        from core.schemas import StrategyDecision

        strategy = StrategyDecision(
            mode="bloqueado",
            direction="flat",
            timeframe=tf_norm or "n/a",
            confidence=0.0,
            operational_status="agent_critical_failure",
            reasons=[reason],
        )
        governance = SentinelGovernanceDecision(
            signal_id=sid,
            regime_id="unknown",
            regime_version="unknown",
            sentinel_decision="block",
            sentinel_confidence=99.0,
            block_reason_code="agent_critical_failure",
            expected_confidence_delta=0.0,
            approved=False,
            reason_codes=[reason],
            risk_flags=[f.agent_name for f in agent_failures if f.is_critical],
        )
        alert = OpportunityAlert(
            asset=asset,
            score=0.0,
            classification="RISCO",
            explanation=f"Pipeline bloqueado: {reason}",
            sources=[],
            strategy=strategy,
            governance=governance,
            chart_timeframe=tf_norm,
            agent_failures=list(agent_failures),
            integrity_score=float(integrity_score),
            fast_path_decision="block",
        )
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
