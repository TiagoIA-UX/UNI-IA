import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import types
import importlib.util


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if "pydantic" not in sys.modules and importlib.util.find_spec("pydantic") is None:
    pydantic_stub = types.ModuleType("pydantic")

    class _BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def dict(self):
            return dict(self.__dict__)

    pydantic_stub.BaseModel = _BaseModel
    sys.modules["pydantic"] = pydantic_stub


from api.desk import PrivateDesk
from api.signal_scanner import SignalScanner
from core.schemas import OpportunityAlert, StrategyDecision, model_to_dict
from core.system_state import SystemStateManager, SystemStatus, UniIAMode


class _FakeCopyTradeService:
    def __init__(self):
        self.executions = []
        self.manual_calls = []

    def status(self):
        return {"enabled": True, "broker_ready": True, "provider": "fake"}

    def execute_from_alert(self, alert):
        self.executions.append(alert.asset)
        return {"success": True, "asset": alert.asset}

    def execute_manual_order(self, **kwargs):
        self.manual_calls.append(kwargs)
        sym = kwargs.get("symbol", "?")
        return {"success": True, "payload": {"symbol": sym}, "broker_response": {"ok": True}}


class _FakeAuditService:
    def __init__(self):
        self.events = []

    def log_event(self, event_type, status, **payload):
        self.events.append((event_type, status, payload))


class _FakeDeskStore:
    def __init__(self):
        self.rows = {}

    def is_ready(self):
        return True

    def create_request(self, payload):
        self.rows[payload["request_id"]] = dict(payload)
        return self.rows[payload["request_id"]]

    def list_pending(self):
        return [row for row in self.rows.values() if row["status"] == "pending_approval"]

    def get_request(self, request_id):
        return self.rows.get(request_id)

    def mark_executed(self, request_id, execution):
        row = self.rows.get(request_id)
        if not row or row["status"] != "pending_approval":
            raise RuntimeError("Request da mesa nao encontrada ou nao esta mais pendente.")
        row["status"] = "executed"
        row["execution"] = execution
        return row

    def mark_rejected(self, request_id, reason):
        row = self.rows.get(request_id)
        if not row or row["status"] != "pending_approval":
            raise RuntimeError("Request da mesa nao encontrada ou nao esta mais pendente.")
        row["status"] = "rejected"
        row["reason"] = reason
        return row


class _NotReadyDeskStore(_FakeDeskStore):
    def is_ready(self):
        return False


class _FakeTelegramBot:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def dispatch_alert(self, alert, operational_context=None):
        if self.should_fail:
            raise RuntimeError("telegram_dispatch_failed")
        return {"success": True, "dispatched": True, "gate_reason": None, "error": None}


class _FakeAnalysisService:
    def __init__(self, alert):
        self.alert = alert
        self.last_signal_id = None

    def analyze(self, asset, signal_id=None):
        self.last_signal_id = signal_id
        return self.alert


class _FakeAnalysisServiceWithTimeframe:
    def __init__(self, alert):
        self.alert = alert
        self.calls = []

    def analyze(self, asset, signal_id=None, chart_timeframe=None):
        self.calls.append((asset, chart_timeframe, signal_id))
        if self.alert.strategy:
            self.alert.strategy.timeframe = chart_timeframe or self.alert.strategy.timeframe
        self.alert.chart_timeframe = chart_timeframe
        return self.alert


class _FailingIntegrityGuard:
    def validate_dispatch_ready(self, alert):
        raise RuntimeError("execution_integrity_failed")


class DeskAndScannerTests(unittest.TestCase):
    def setUp(self):
        self.alert = OpportunityAlert(
            asset="BTCUSDT",
            score=90,
            classification="OPORTUNIDADE",
            explanation="Confluencia forte a favor da tendencia.",
            sources=["test"],
        )
        self.base_env = {
            "DESK_MIN_SCORE": "75",
            "DESK_ALLOWED_ASSETS": "BTCUSDT",
            # Isola suite do ambiente do SO: quando definido, vale mais que UNI_IA_REQUIRE_APPROVAL
            "DESK_REQUIRE_MANUAL_APPROVAL": "",
            "UNI_IA_REQUIRE_APPROVAL": "true",
            "SIGNAL_MIN_SCORE": "75",
            "SIGNAL_ALLOWED_CLASSIFICATIONS": "OPORTUNIDADE",
            "SIGNAL_SCAN_ASSETS": "BTCUSDT",
            "SIGNAL_SCANNER_ENABLED": "true",
        }

    def _build_desk(self, mode, status):
        state = SystemStateManager(UniIAMode(mode))
        state.status = SystemStatus(status)
        return (
            PrivateDesk(
                copy_trade_service=_FakeCopyTradeService(),
                audit_service=_FakeAuditService(),
                desk_store=_FakeDeskStore(),
                system_state=state,
            ),
            state,
        )

    def test_approval_approve_does_not_execute_real_order(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "approval"}, clear=False):
            desk, _ = self._build_desk("approval", "ready")
            pending = desk.handle_alert(self.alert)
            result = desk.approve(pending["request_id"])

        self.assertEqual(result["execution"]["decision"], "approved_without_live_execution")
        self.assertEqual(desk.copy_trade_service.executions, [])

    def test_live_ready_approve_executes_real_order(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live", "UNI_IA_REQUIRE_APPROVAL": "true"}, clear=False):
            desk, _ = self._build_desk("live", "ready")
            pending = desk.handle_alert(self.alert)
            result = desk.approve(pending["request_id"])

        self.assertTrue(result["execution"]["success"])
        self.assertEqual(desk.copy_trade_service.executions, ["BTCUSDT"])

    def test_live_locked_approve_fails(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live", "UNI_IA_REQUIRE_APPROVAL": "true"}, clear=False):
            desk, _ = self._build_desk("live", "locked")
            desk.desk_store.rows["req-1"] = {
                "request_id": "req-1",
                "asset": "BTCUSDT",
                "score": 90,
                "classification": "OPORTUNIDADE",
                "alert": model_to_dict(self.alert),
                "status": "pending_approval",
            }
            with self.assertRaises(RuntimeError):
                desk.approve("req-1")

    def test_double_approval_does_not_duplicate_execution(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live", "UNI_IA_REQUIRE_APPROVAL": "true"}, clear=False):
            desk, _ = self._build_desk("live", "ready")
            pending = desk.handle_alert(self.alert)
            desk.approve(pending["request_id"])

            with self.assertRaises(RuntimeError):
                desk.approve(pending["request_id"])

        self.assertEqual(desk.copy_trade_service.executions, ["BTCUSDT"])

    def test_preview_action_blocks_when_system_cannot_generate_signal(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "paper"}, clear=False):
            desk, _ = self._build_desk("paper", "halted")
            preview = desk.preview_action(self.alert)

        self.assertEqual(preview["action"], "blocked")
        self.assertIn("Sistema bloqueado para gerar sinais", preview["operational_status"])

    def test_preview_action_blocks_live_when_execution_is_not_allowed(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live", "UNI_IA_REQUIRE_APPROVAL": "false"}, clear=False):
            desk, _ = self._build_desk("live", "degraded")
            preview = desk.preview_action(self.alert)

        self.assertEqual(preview["action"], "blocked")
        self.assertIn("Execucao real bloqueada", preview["operational_status"])

    def test_desk_require_manual_approval_overrides_uni_ia_when_set(self):
        """INSTALLATION refere DESK_REQUIRE_MANUAL_APPROVAL; deve prevalecer se definido."""
        with patch.dict(
            "os.environ",
            {
                **self.base_env,
                "UNI_IA_MODE": "live",
                "UNI_IA_REQUIRE_APPROVAL": "false",
                "DESK_REQUIRE_MANUAL_APPROVAL": "true",
            },
            clear=False,
        ):
            desk, _ = self._build_desk("live", "ready")
            cfg = desk.status()["desk"]
        self.assertTrue(cfg["manual_approval"])

    def test_desk_require_false_turns_off_manual_when_explicit(self):
        with patch.dict(
            "os.environ",
            {
                **self.base_env,
                "UNI_IA_MODE": "live",
                "UNI_IA_REQUIRE_APPROVAL": "true",
                "DESK_REQUIRE_MANUAL_APPROVAL": "false",
            },
            clear=False,
        ):
            desk, _ = self._build_desk("live", "ready")
            cfg = desk.status()["desk"]
        self.assertFalse(cfg["manual_approval"])

    def test_scanner_strict_operational_mode_falls_back_to_desk_mode(self):
        """Quando `UNI_IA_MODE` esta vazio, o scanner alinha ao `DESK_MODE` (ex.: .env legado)."""
        desk, _ = self._build_desk("paper", "ready")
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "", "DESK_MODE": "live"}, clear=False):
            scanner = SignalScanner(
                analysis_service=_FakeAnalysisService(self.alert),
                telegram_bot=_FakeTelegramBot(),
                private_desk=desk,
                audit_service=_FakeAuditService(),
                system_state=None,
            )
            self.assertTrue(scanner._strict_operational_mode())

    def test_scanner_marks_dispatch_blocked_when_telegram_gate_suppresses(self):
        state = SystemStateManager(UniIAMode.PAPER)
        state.status = SystemStatus.READY
        alert = OpportunityAlert(
            asset="BTCUSDT",
            score=90,
            classification="OPORTUNIDADE",
            explanation="Setup.",
            sources=["test"],
            strategy=StrategyDecision(
                mode="swing",
                direction="long",
                timeframe="1h",
                confidence=80.0,
                operational_status="ok",
                reasons=["test"],
            ),
        )

        class _GateBot:
            def dispatch_alert(self, alert, operational_context=None):
                return {
                    "success": True,
                    "dispatched": False,
                    "gate_reason": "fast_path_block",
                    "error": None,
                }

        recorded = []

        def _capture(**kw):
            recorded.append(dict(kw))

        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "paper"}, clear=False):
            desk = PrivateDesk(
                copy_trade_service=_FakeCopyTradeService(),
                audit_service=_FakeAuditService(),
                desk_store=_FakeDeskStore(),
                system_state=state,
            )
            scanner = SignalScanner(
                analysis_service=_FakeAnalysisService(alert),
                telegram_bot=_GateBot(),
                private_desk=desk,
                audit_service=_FakeAuditService(),
                system_state=state,
            )
            with patch.object(scanner, "_record_dispatch_event", side_effect=_capture):
                scanner.scan_asset("BTCUSDT")

        self.assertTrue(recorded)
        self.assertEqual(recorded[-1]["status"], "blocked")

    def test_scanner_locked_returns_blocked(self):
        state = SystemStateManager(UniIAMode.LIVE)
        state.status = SystemStatus.LOCKED
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live"}, clear=False):
            desk = PrivateDesk(
                copy_trade_service=_FakeCopyTradeService(),
                audit_service=_FakeAuditService(),
                desk_store=_FakeDeskStore(),
                system_state=state,
            )
            scanner = SignalScanner(
                analysis_service=_FakeAnalysisService(self.alert),
                telegram_bot=_FakeTelegramBot(),
                private_desk=desk,
                audit_service=_FakeAuditService(),
                system_state=state,
            )
            result = scanner.scan_asset("BTCUSDT")

        self.assertEqual(result["desk_action"], "blocked")
        self.assertEqual(result["reason"], "sistema_locked")

    def test_scanner_live_blocks_on_telegram_failure(self):
        state = SystemStateManager(UniIAMode.LIVE)
        state.status = SystemStatus.READY
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live"}, clear=False):
            copy_trade = _FakeCopyTradeService()
            analysis = _FakeAnalysisService(self.alert)
            desk = PrivateDesk(
                copy_trade_service=copy_trade,
                audit_service=_FakeAuditService(),
                desk_store=_FakeDeskStore(),
                system_state=state,
            )
            scanner = SignalScanner(
                analysis_service=analysis,
                telegram_bot=_FakeTelegramBot(should_fail=True),
                private_desk=desk,
                audit_service=_FakeAuditService(),
                system_state=state,
            )
            result = scanner.scan_asset("BTCUSDT")

        self.assertIn("telegram_dispatch_failed", result["error"])
        self.assertEqual(analysis.last_signal_id, result["signal_id"])
        self.assertEqual(copy_trade.executions, [])

    def test_scanner_blocks_dispatch_when_execution_integrity_fails(self):
        state = SystemStateManager(UniIAMode.LIVE)
        state.status = SystemStatus.READY
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live"}, clear=False):
            copy_trade = _FakeCopyTradeService()
            desk = PrivateDesk(
                copy_trade_service=copy_trade,
                audit_service=_FakeAuditService(),
                desk_store=_FakeDeskStore(),
                system_state=state,
            )
            scanner = SignalScanner(
                analysis_service=_FakeAnalysisService(self.alert),
                telegram_bot=_FakeTelegramBot(),
                private_desk=desk,
                audit_service=_FakeAuditService(),
                system_state=state,
                integrity_guard=_FailingIntegrityGuard(),
            )
            result = scanner.scan_asset("BTCUSDT")

        self.assertIn("execution_integrity_failed", result["error"])
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertEqual(result["error_stage"], "integrity_guard")
        self.assertEqual(copy_trade.executions, [])

    def test_scanner_scans_configured_timeframes_once_per_closed_candle(self):
        from core.schemas import StrategyDecision

        state = SystemStateManager(UniIAMode.PAPER)
        state.status = SystemStatus.READY
        alert = OpportunityAlert(
            asset="BTCUSDT",
            score=90,
            classification="OPORTUNIDADE",
            explanation="Setup confirmado no fechamento do candle.",
            sources=["test"],
            strategy=StrategyDecision(
                mode="fast_scalp",
                direction="long",
                timeframe="5m",
                confidence=90,
                operational_status="confirmed",
                reasons=["closed_candle_confirmed"],
            ),
            chart_timeframe="5m",
        )
        env = {
            **self.base_env,
            "UNI_IA_MODE": "paper",
            "SIGNAL_SCAN_TIMEFRAMES": "5m,15m",
            "SIGNAL_SCAN_STAGGER_SECONDS": "0",
            "SIGNAL_CANDLE_CLOSE_GRACE_SECONDS": "0",
        }
        with patch.dict("os.environ", env, clear=False):
            desk = PrivateDesk(
                copy_trade_service=_FakeCopyTradeService(),
                audit_service=_FakeAuditService(),
                desk_store=_FakeDeskStore(),
                system_state=state,
            )
            analysis = _FakeAnalysisServiceWithTimeframe(alert)
            scanner = SignalScanner(
                analysis_service=analysis,
                telegram_bot=_FakeTelegramBot(),
                private_desk=desk,
                audit_service=_FakeAuditService(),
                system_state=state,
            )

            first = scanner.run_cycle()
            second = scanner.run_cycle()

        self.assertEqual([call[1] for call in analysis.calls], ["5m", "15m"])
        self.assertEqual(len(first["results"]), 2)
        self.assertTrue(all(item["dispatched"] for item in first["results"]))
        self.assertEqual([item["reason"] for item in second["results"]], ["candle_ja_confirmado", "candle_ja_confirmado"])

    def test_reject_in_memory_requires_pending_status(self):
        state = SystemStateManager(UniIAMode.APPROVAL)
        state.status = SystemStatus.READY
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "approval"}, clear=False):
            desk = PrivateDesk(
                copy_trade_service=_FakeCopyTradeService(),
                audit_service=_FakeAuditService(),
                desk_store=_NotReadyDeskStore(),
                system_state=state,
            )
            desk.pending_requests["req-1"] = {
                "request_id": "req-1",
                "asset": "BTCUSDT",
                "score": 90,
                "classification": "OPORTUNIDADE",
                "alert": model_to_dict(self.alert),
                "status": "executed",
            }

            with self.assertRaises(RuntimeError):
                desk.reject("req-1")

    def test_manual_order_paper_simulated(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "paper"}, clear=False):
            desk, _ = self._build_desk("paper", "ready")
            out = desk.execute_manual_order(asset="BTC-USDT", side="BUY", risk_percent=1.0, source="test")

        self.assertEqual(out["action"], "paper_simulated")
        self.assertEqual(desk.copy_trade_service.manual_calls, [])

    def test_manual_order_live_calls_broker(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "live", "UNI_IA_REQUIRE_APPROVAL": "false"}, clear=False):
            copy_trade = _FakeCopyTradeService()
            state = SystemStateManager(UniIAMode.LIVE)
            state.status = SystemStatus.READY
            desk = PrivateDesk(
                copy_trade_service=copy_trade,
                audit_service=_FakeAuditService(),
                desk_store=_FakeDeskStore(),
                system_state=state,
            )
            out = desk.execute_manual_order(asset="BTC-USDT", side="COMPRA", source="test")

        self.assertEqual(out["action"], "executed")
        self.assertEqual(len(copy_trade.manual_calls), 1)
        self.assertEqual(copy_trade.manual_calls[0]["symbol"], "BTCUSDT")

    def test_manual_order_approval_raises(self):
        with patch.dict("os.environ", {**self.base_env, "UNI_IA_MODE": "approval"}, clear=False):
            desk, _ = self._build_desk("approval", "ready")
            with self.assertRaises(RuntimeError):
                desk.execute_manual_order(asset="BTCUSDT", side="BUY")


if __name__ == "__main__":
    unittest.main()
