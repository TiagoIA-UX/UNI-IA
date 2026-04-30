import os
import uuid
from datetime import datetime
from typing import Any, Dict, List

from core.schemas import OpportunityAlert


class PrivateDesk:
    """Mesa privada com controle operacional e governanca de execucao.

    Regras principais:
    - modo paper/live
    - score minimo e classificacao elegivel
    - whitelist de ativos
    - aprovacao manual opcional antes de enviar para copy trade
    """

    def __init__(self, copy_trade_service, audit_service=None):
        self.copy_trade_service = copy_trade_service
        self.audit_service = audit_service
        self.pending_requests: Dict[str, Dict[str, Any]] = {}

    def _audit(self, event_type: str, status: str, **payload):
        if not self.audit_service:
            return
        try:
            self.audit_service.log_event(event_type, status, **payload)
        except Exception as err:
            print(f"[AUDIT][WARN] {event_type}: {err}")

    def _cfg(self) -> Dict[str, Any]:
        allowed_raw = os.getenv("DESK_ALLOWED_ASSETS", "")
        allowed_assets = [a.strip().upper() for a in allowed_raw.split(",") if a.strip()]
        return {
            "mode": os.getenv("DESK_MODE", "paper").lower(),  # paper | live
            "manual_approval": os.getenv("DESK_REQUIRE_MANUAL_APPROVAL", "true").lower() == "true",
            "min_score": float(os.getenv("DESK_MIN_SCORE", "75")),
            "allowed_assets": allowed_assets,
        }

    def status(self) -> Dict[str, Any]:
        cfg = self._cfg()
        return {
            "desk": cfg,
            "copy_trade": self.copy_trade_service.status(),
            "pending_count": len(self.pending_requests),
        }

    def preview_action(self, alert: OpportunityAlert) -> Dict[str, Any]:
        cfg = self._cfg()
        try:
            self._validate_alert(alert, cfg)
        except Exception as err:
            return {
                "mode": cfg["mode"],
                "action": "blocked",
                "operational_status": str(err),
            }

        if cfg["mode"] != "live":
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
        return list(self.pending_requests.values())

    def _is_asset_allowed(self, asset: str, allowed_assets: List[str]) -> bool:
        if not allowed_assets:
            return True
        normalized = (asset or "").upper()
        return normalized in allowed_assets

    def _validate_alert(self, alert: OpportunityAlert, cfg: Dict[str, Any]):
        if alert.classification != "OPORTUNIDADE":
            raise RuntimeError("Mesa bloqueou execucao: apenas OPORTUNIDADE pode seguir para mesa.")
        if float(alert.score) < cfg["min_score"]:
            raise RuntimeError(f"Mesa bloqueou execucao: score abaixo do minimo ({alert.score} < {cfg['min_score']}).")
        if not self._is_asset_allowed(alert.asset, cfg["allowed_assets"]):
            raise RuntimeError(f"Mesa bloqueou execucao: ativo fora da whitelist ({alert.asset}).")

    def handle_alert(self, alert: OpportunityAlert) -> Dict[str, Any]:
        cfg = self._cfg()
        self._validate_alert(alert, cfg)

        # Paper mode nunca envia ordem real
        if cfg["mode"] != "live":
            self._audit(
                "desk.paper_logged",
                "success",
                asset=alert.asset,
                classification=alert.classification,
                score=float(alert.score),
                details={"mode": cfg["mode"], "strategy": alert.strategy.dict() if alert.strategy else None},
            )
            return {
                "success": True,
                "mode": cfg["mode"],
                "action": "paper_logged",
                "message": "Sinal aprovado pela mesa e registrado em paper mode.",
            }

        # Live + aprovacao manual -> pendencia
        if cfg["manual_approval"]:
            request_id = str(uuid.uuid4())
            self.pending_requests[request_id] = {
                "request_id": request_id,
                "asset": alert.asset,
                "score": alert.score,
                "classification": alert.classification,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "alert": alert.dict(),
                "status": "pending_approval",
            }
            self._audit(
                "desk.pending_approval",
                "pending",
                asset=alert.asset,
                request_id=request_id,
                classification=alert.classification,
                score=float(alert.score),
                details={"mode": cfg["mode"], "strategy": alert.strategy.dict() if alert.strategy else None},
            )
            return {
                "success": True,
                "mode": cfg["mode"],
                "action": "pending_approval",
                "request_id": request_id,
                "message": "Sinal aguardando aprovacao manual da mesa.",
            }

        # Live sem aprovacao manual: executa direto no copy trade
        result = self.copy_trade_service.execute_from_alert(alert)
        self._audit(
            "desk.executed",
            "success",
            asset=alert.asset,
            classification=alert.classification,
            score=float(alert.score),
            details={"mode": cfg["mode"], "execution": result, "strategy": alert.strategy.dict() if alert.strategy else None},
        )
        return {
            "success": True,
            "mode": cfg["mode"],
            "action": "executed",
            "execution": result,
        }

    def approve(self, request_id: str) -> Dict[str, Any]:
        req = self.pending_requests.get(request_id)
        if not req:
            raise RuntimeError("Request de aprovacao nao encontrada.")
        if req.get("status") != "pending_approval":
            raise RuntimeError("Request nao esta pendente para aprovacao.")

        alert = OpportunityAlert(**req["alert"])
        result = self.copy_trade_service.execute_from_alert(alert)

        req["status"] = "executed"
        req["executed_at"] = datetime.utcnow().isoformat() + "Z"
        req["execution"] = result
        self._audit(
            "desk.approved_execution",
            "success",
            asset=alert.asset,
            request_id=request_id,
            classification=alert.classification,
            score=float(alert.score),
            details={"execution": result, "strategy": alert.strategy.dict() if alert.strategy else None},
        )

        return {
            "success": True,
            "request_id": request_id,
            "action": "executed",
            "execution": result,
        }

    def reject(self, request_id: str, reason: str = "rejeitado pela mesa") -> Dict[str, Any]:
        req = self.pending_requests.get(request_id)
        if not req:
            raise RuntimeError("Request de aprovacao nao encontrada.")
        req["status"] = "rejected"
        req["rejected_at"] = datetime.utcnow().isoformat() + "Z"
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
