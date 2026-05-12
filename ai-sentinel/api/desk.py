import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.contract_validation import normalize_classification
from core.schemas import OpportunityAlert, model_to_dict


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class PrivateDesk:
    """Mesa privada com controle operacional e governanca de execucao.

    Regras principais:
    - modo paper/live
    - score minimo e classificacao elegivel
    - whitelist de ativos
    - aprovacao manual opcional antes de enviar para copy trade
    """

    def __init__(self, copy_trade_service, audit_service=None, desk_store=None, system_state=None):
        self.copy_trade_service = copy_trade_service
        self.audit_service = audit_service
        self.desk_store = desk_store
        self.system_state = system_state
        self.pending_requests: Dict[str, Dict[str, Any]] = {}

    def _audit(self, event_type: str, status: str, **payload):
        if not self.audit_service:
            return {"success": False, "reason": "audit_service_ausente"}

        audit_result = self.audit_service.log_event(event_type, status, **payload)
        if audit_result is None:
            audit_result = {"success": True}
        if self._audit_required() and not audit_result.get("success"):
            raise RuntimeError(
                f"Auditoria obrigatoria falhou em {event_type}: {audit_result.get('reason', 'falha_desconhecida')}"
            )
        return audit_result

    def _runtime_mode(self) -> str:
        if self.system_state:
            return self.system_state.mode.value
        return os.getenv("UNI_IA_MODE", "paper").lower()

    def _audit_required(self) -> bool:
        return self._runtime_mode() in {"approval", "live"}

    @staticmethod
    def _env_flag_true(value: Optional[str]) -> bool:
        if value is None or not str(value).strip():
            return False
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def _env_flag_false(value: Optional[str]) -> bool:
        if value is None or not str(value).strip():
            return False
        return str(value).strip().lower() in ("0", "false", "no", "off")

    def _cfg(self) -> Dict[str, Any]:
        allowed_raw = os.getenv("DESK_ALLOWED_ASSETS", "")
        allowed_assets = [a.strip().upper() for a in allowed_raw.split(",") if a.strip()]
        mode = self.system_state.mode.value if self.system_state else os.getenv("UNI_IA_MODE", "paper").lower()

        # INSTALLATION/.env.example documentam DESK_REQUIRE_MANUAL_APPROVAL; quando definido,
        # prevalece sobre UNI_IA_REQUIRE_APPROVAL (alias legível da mesma regra).
        desk_raw = os.getenv("DESK_REQUIRE_MANUAL_APPROVAL", "").strip()
        if desk_raw != "":
            if self._env_flag_true(desk_raw):
                require_approval = True
            elif self._env_flag_false(desk_raw):
                require_approval = False
            else:
                require_approval = os.getenv("UNI_IA_REQUIRE_APPROVAL", "true").lower() == "true"
        else:
            require_approval = os.getenv("UNI_IA_REQUIRE_APPROVAL", "true").lower() == "true"

        return {
            "mode": mode,
            "manual_approval": require_approval or mode == "approval",
            "min_score": float(os.getenv("DESK_MIN_SCORE", "75")),
            "allowed_assets": allowed_assets,
        }

    def status(self) -> Dict[str, Any]:
        cfg = self._cfg()
        pending = self.list_pending()
        return {
            "desk": cfg,
            "copy_trade": self.copy_trade_service.status(),
            "system": self.system_state.snapshot() if self.system_state else None,
            "persistence_ready": bool(self.desk_store and self.desk_store.is_ready()),
            "pending_count": len(pending),
        }

    def preview_action(self, alert: OpportunityAlert) -> Dict[str, Any]:
        cfg = self._cfg()
        try:
            if self.system_state:
                if cfg["mode"] == "paper":
                    self.system_state.require_signal_generation()
                elif cfg["manual_approval"]:
                    self.system_state.require_pending_creation()
                else:
                    self.system_state.require_live_execution()
            self._validate_alert(alert, cfg)
        except Exception as err:
            return {
                "mode": cfg["mode"],
                "action": "blocked",
                "operational_status": str(err),
            }

        if cfg["mode"] != "live":
            if cfg["mode"] == "approval":
                return {
                    "mode": cfg["mode"],
                    "action": "pending_approval",
                    "operational_status": "aguardando_aprovacao_manual",
                }
            return {
                "mode": cfg["mode"],
                "action": "paper_logged",
                "operational_status": "paper_mode",
            }

        if cfg["manual_approval"]:
            return {
                "mode": cfg["mode"],
                "action": "pending_approval",
                "operational_status": "aguardando_aprovacao_manual",
            }

        return {
            "mode": cfg["mode"],
            "action": "executed",
            "operational_status": "execucao_automatica_habilitada",
        }

    def list_pending(self) -> List[Dict[str, Any]]:
        if self.desk_store and self.desk_store.is_ready():
            return self.desk_store.list_pending()
        return list(self.pending_requests.values())

    def _load_request(self, request_id: str) -> Dict[str, Any]:
        if self.desk_store and self.desk_store.is_ready():
            req = self.desk_store.get_request(request_id)
        else:
            req = self.pending_requests.get(request_id)
        if not req:
            raise RuntimeError("Request de aprovacao nao encontrada.")
        return req

    @staticmethod
    def _normalize_desk_asset_key(asset: str) -> str:
        return (asset or "").strip().upper().replace("-", "").replace("/", "").replace("_", "")

    def _is_asset_allowed(self, asset: str, allowed_assets: List[str]) -> bool:
        if not allowed_assets:
            return True
        n = self._normalize_desk_asset_key(asset)
        for a in allowed_assets:
            if self._normalize_desk_asset_key(a) == n:
                return True
        return False

    @staticmethod
    def normalize_trading_symbol(asset: str) -> str:
        """Alinha simbolos da UI (BTC-BRL, BTCBRL) ao formato esperado pelo broker."""
        a = (asset or "").strip().upper().replace("-", "").replace("/", "").replace("_", "")
        if not a:
            raise RuntimeError("Ativo vazio.")
        if a.endswith("USDT"):
            return a
        if a.endswith("BRL"):
            return a
        if a.isalpha() and 2 <= len(a) <= 6:
            return f"{a}BRL"
        return a

    def _validate_alert(self, alert: OpportunityAlert, cfg: Dict[str, Any]):
        if alert.governance and not alert.governance.approved:
            raise RuntimeError(
                f"Mesa bloqueou execucao: SENTINEL:{alert.governance.block_reason_code}."
            )
        if normalize_classification(alert.classification) != "OPORTUNIDADE":
            raise RuntimeError("Mesa bloqueou execucao: apenas OPORTUNIDADE pode seguir para mesa.")
        if float(alert.score) < cfg["min_score"]:
            raise RuntimeError(f"Mesa bloqueou execucao: score abaixo do minimo ({alert.score} < {cfg['min_score']}).")
        if not self._is_asset_allowed(alert.asset, cfg["allowed_assets"]):
            raise RuntimeError(f"Mesa bloqueou execucao: ativo fora da whitelist ({alert.asset}).")

    def handle_alert(self, alert: OpportunityAlert) -> Dict[str, Any]:
        cfg = self._cfg()
        if self.system_state:
            self.system_state.require_signal_generation()
        self._validate_alert(alert, cfg)

        # Paper mode nunca envia ordem real
        if cfg["mode"] == "paper":
            self._audit(
                "desk.paper_logged",
                "success",
                asset=alert.asset,
                classification=alert.classification,
                score=float(alert.score),
                details={"mode": cfg["mode"], "strategy": model_to_dict(alert.strategy) if alert.strategy else None},
            )
            return {
                "success": True,
                "mode": cfg["mode"],
                "action": "paper_logged",
                "message": "Sinal aprovado pela mesa e registrado em paper mode.",
            }

        # Approval/live com aprovacao manual -> pendencia
        if cfg["manual_approval"]:
            if self.system_state:
                self.system_state.require_pending_creation()
            request_id = str(uuid.uuid4())
            request_payload = {
                "request_id": request_id,
                "asset": alert.asset,
                "score": alert.score,
                "classification": alert.classification,
                "created_at": _utc_now_iso(),
                "alert": model_to_dict(alert),
                "status": "pending_approval",
            }
            self._audit(
                "desk.pending_approval",
                "pending",
                asset=alert.asset,
                request_id=request_id,
                classification=alert.classification,
                score=float(alert.score),
                details={"mode": cfg["mode"], "strategy": model_to_dict(alert.strategy) if alert.strategy else None},
            )
            if self.desk_store and self.desk_store.is_ready():
                self.desk_store.create_request(request_payload)
            else:
                self.pending_requests[request_id] = request_payload
            return {
                "success": True,
                "mode": cfg["mode"],
                "action": "pending_approval",
                "request_id": request_id,
                "message": "Sinal aguardando aprovacao manual da mesa.",
            }

        # Live sem aprovacao manual: executa direto no copy trade
        if self.system_state:
            self.system_state.require_live_execution()
        self._audit(
            "desk.execution_requested",
            "pending",
            asset=alert.asset,
            classification=alert.classification,
            score=float(alert.score),
            details={"mode": cfg["mode"], "strategy": model_to_dict(alert.strategy) if alert.strategy else None},
        )
        result = self.copy_trade_service.execute_from_alert(alert)
        self._audit(
            "desk.executed",
            "success",
            asset=alert.asset,
            classification=alert.classification,
            score=float(alert.score),
            details={"mode": cfg["mode"], "execution": result, "strategy": model_to_dict(alert.strategy) if alert.strategy else None},
        )
        return {
            "success": True,
            "mode": cfg["mode"],
            "action": "executed",
            "execution": result,
        }

    def approve(self, request_id: str) -> Dict[str, Any]:
        req = self._load_request(request_id)
        if req.get("status") != "pending_approval":
            raise RuntimeError("Request nao esta pendente para aprovacao.")

        alert = OpportunityAlert(**req["alert"])
        cfg = self._cfg()
        if cfg["mode"] == "live":
            if self.system_state:
                self.system_state.require_live_execution()
            self._audit(
                "desk.approval_granted",
                "pending",
                asset=alert.asset,
                request_id=request_id,
                classification=alert.classification,
                score=float(alert.score),
                details={"mode": cfg["mode"], "strategy": model_to_dict(alert.strategy) if alert.strategy else None},
            )
            result = self.copy_trade_service.execute_from_alert(alert)
        else:
            result = {
                "success": True,
                "mode": cfg["mode"],
                "live_execution": False,
                "decision": "approved_without_live_execution",
            }

        if self.desk_store and self.desk_store.is_ready():
            req = self.desk_store.mark_executed(request_id, result)
        else:
            req["status"] = "executed"
            req["executed_at"] = _utc_now_iso()
            req["execution"] = result
        self._audit(
            "desk.approved_execution",
            "success",
            asset=alert.asset,
            request_id=request_id,
            classification=alert.classification,
            score=float(alert.score),
            details={"execution": result, "strategy": model_to_dict(alert.strategy) if alert.strategy else None},
        )

        return {
            "success": True,
            "request_id": request_id,
            "action": "executed",
            "execution": result,
        }

    def reject(self, request_id: str, reason: str = "rejeitado pela mesa") -> Dict[str, Any]:
        req = self._load_request(request_id)
        if self.desk_store and self.desk_store.is_ready():
            req = self.desk_store.mark_rejected(request_id, reason)
        else:
            if req.get("status") != "pending_approval":
                raise RuntimeError("Request nao esta pendente para rejeicao.")
            req["status"] = "rejected"
            req["rejected_at"] = _utc_now_iso()
            req["reason"] = reason
        self._audit(
            "desk.rejected",
            "rejected",
            asset=req.get("asset"),
            request_id=request_id,
            classification=req.get("classification"),
            score=float(req.get("score", 0)),
            details={"reason": reason},
        )
        return {
            "success": True,
            "request_id": request_id,
            "action": "rejected",
            "reason": reason,
        }

    def execute_manual_order(
        self,
        *,
        asset: str,
        side: str,
        risk_percent: float = 1.0,
        source: str = "plataforma-web",
        quantity: Optional[str] = None,
        chart_timeframe: Optional[str] = None,
        auto_mode_context: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Ordem disparada pela UI ou integracao externa (nao passa pelo pipeline de alerta)."""
        cfg = self._cfg()
        norm_asset = self.normalize_trading_symbol(asset)
        side_raw = (side or "").strip().upper()
        if side_raw in ("COMPRA", "BUY"):
            side_u = "BUY"
        elif side_raw in ("VENDA", "SELL"):
            side_u = "SELL"
        else:
            raise RuntimeError("Lado invalido: use BUY ou SELL (COMPRA/VENDA aceitos).")

        if not self._is_asset_allowed(norm_asset, cfg["allowed_assets"]):
            raise RuntimeError(
                f"Ativo {norm_asset} fora da whitelist DESK_ALLOWED_ASSETS."
            )

        details: Dict[str, Any] = {
            "symbol": norm_asset,
            "side": side_u,
            "risk_percent": risk_percent,
            "source": source,
            "chart_timeframe": chart_timeframe,
            "auto_mode_context": auto_mode_context,
        }

        if cfg["mode"] == "paper":
            self._audit(
                "desk.manual_paper",
                "success",
                asset=norm_asset,
                classification="MANUAL",
                score=0.0,
                details=details,
            )
            return {
                "success": True,
                "mode": cfg["mode"],
                "action": "paper_simulated",
                "symbol": norm_asset,
                "side": side_u,
                "message": (
                    "Paper: ordem nao enviada ao broker. "
                    "Para real no Mercado Bitcoin: UNI_IA_MODE=live, credenciais MB e ativo na whitelist."
                ),
            }

        if cfg["mode"] == "approval":
            self._audit(
                "desk.manual_blocked_approval_mode",
                "blocked",
                asset=norm_asset,
                classification="MANUAL",
                score=0.0,
                details=details,
            )
            raise RuntimeError(
                "Modo approval: a plataforma nao envia ordem manual direta. "
                "Use UNI_IA_MODE=live para execucao manual real via broker, "
                "ou o fluxo de sinais IA com aprovacao na mesa (pending/approve)."
            )

        if self.system_state:
            self.system_state.require_live_execution()

        self._audit(
            "desk.manual_execution_requested",
            "pending",
            asset=norm_asset,
            classification="MANUAL",
            score=0.0,
            details=details,
        )
        result = self.copy_trade_service.execute_manual_order(
            symbol=norm_asset,
            side=side_u,
            quantity=quantity,
            risk_percent=risk_percent,
            meta={
                "source": source,
                "chart_timeframe": chart_timeframe,
                "auto_mode_context": auto_mode_context,
            },
        )
        self._audit(
            "desk.manual_executed",
            "success",
            asset=norm_asset,
            classification="MANUAL",
            score=0.0,
            details={**details, "execution": result},
        )
        return {
            "success": True,
            "mode": cfg["mode"],
            "action": "executed",
            "symbol": norm_asset,
            "side": side_u,
            "execution": result,
            "message": "Ordem enviada ao broker.",
        }
