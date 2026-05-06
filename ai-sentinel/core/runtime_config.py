import os
from typing import List

from core.system_state import SystemStateManager, UniIAMode


def _is_true(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() == "true"


def get_allowed_origins() -> List[str]:
    raw = os.getenv("UNI_IA_ALLOWED_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_runtime_mode() -> UniIAMode:
    raw = os.getenv("UNI_IA_MODE", UniIAMode.PAPER.value).strip().lower()
    try:
        return UniIAMode(raw)
    except ValueError as exc:
        raise RuntimeError(f"UNI_IA_MODE invalido: {raw}") from exc


def build_system_state(*, copy_trade_service, audit_service, signal_scanner, telegram_control, telegram_bot, desk_store):
    mode = get_runtime_mode()
    strict_operational_mode = mode in {UniIAMode.APPROVAL, UniIAMode.LIVE}
    state = SystemStateManager(mode)
    critical_errors: List[str] = []
    non_critical_errors: List[str] = []

    admin_token = os.getenv("UNI_IA_ADMIN_TOKEN", "").strip()
    if not admin_token:
        critical_errors.append("UNI_IA_ADMIN_TOKEN obrigatorio.")

    allowed_origins = get_allowed_origins()
    if not allowed_origins:
        critical_errors.append("UNI_IA_ALLOWED_ORIGINS nao pode ficar vazio.")
    if "*" in allowed_origins:
        critical_errors.append("UNI_IA_ALLOWED_ORIGINS nao pode usar wildcard '*'.")

    scanner_enabled = _is_true(os.getenv("SIGNAL_SCANNER_ENABLED", "false"))
    telegram_control_enabled = _is_true(os.getenv("TELEGRAM_CONTROL_ENABLED", "false"))
    require_approval = _is_true(os.getenv("UNI_IA_REQUIRE_APPROVAL", "true"), default=True)
    audit_table_name = os.getenv("AUDIT_TABLE_NAME", "").strip()

    if audit_service.is_ready() and not audit_table_name:
        critical_errors.append(
            "Auditoria configurada exige AUDIT_TABLE_NAME definido explicitamente."
        )

    if scanner_enabled and signal_scanner is not None and not signal_scanner.configured():
        critical_errors.append("SIGNAL_SCANNER_ENABLED=true exige SIGNAL_SCAN_ASSETS configurado.")

    if telegram_control_enabled and telegram_control is not None and not telegram_control.configured():
        target = critical_errors if strict_operational_mode else non_critical_errors
        target.append(
            "TELEGRAM_CONTROL_ENABLED=true exige TELEGRAM_BOT_TOKEN e ao menos um admin em "
            "TELEGRAM_ADMIN_CHAT_IDS ou TELEGRAM_ADMIN_USER_IDS."
        )

    if strict_operational_mode and telegram_bot is not None and not telegram_bot.configured():
        critical_errors.append(
            "UNI_IA_MODE=approval/live exige Telegram de dispatch configurado com tokens e canais."
        )

    if mode == UniIAMode.APPROVAL and not desk_store.is_ready():
        critical_errors.append(
            "UNI_IA_MODE=approval exige persistencia da mesa no Supabase para armazenar pendencias."
        )

    if mode == UniIAMode.APPROVAL and not audit_service.is_ready():
        critical_errors.append(
            "UNI_IA_MODE=approval exige auditoria ativa com NEXT_PUBLIC_SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY."
        )

    if audit_service.is_ready() and audit_table_name:
        try:
            audit_service.validate_boot_or_raise()
        except Exception as exc:
            critical_errors.append(f"Auditoria invalida no boot: {exc}")

    if mode == UniIAMode.LIVE:
        if not copy_trade_service.enabled:
            critical_errors.append("UNI_IA_MODE=live exige COPY_TRADE_ENABLED=true.")
        if not copy_trade_service.adapter.is_ready():
            missing = ", ".join(copy_trade_service.adapter.missing_config())
            critical_errors.append(f"UNI_IA_MODE=live exige broker configurado. Faltando: {missing}.")
        if not audit_service.is_ready():
            critical_errors.append(
                "UNI_IA_MODE=live exige auditoria ativa com NEXT_PUBLIC_SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY."
            )
        if require_approval and not desk_store.is_ready():
            missing = ", ".join(desk_store.missing_config())
            critical_errors.append(
                "UNI_IA_REQUIRE_APPROVAL=true em live exige persistencia da mesa no Supabase. "
                f"Faltando: {missing}."
            )

    state.apply_validation_result(
        critical_errors=critical_errors,
        non_critical_errors=non_critical_errors,
    )
    return state


def validate_runtime_or_raise(*, copy_trade_service, audit_service, signal_scanner, telegram_control, telegram_bot, desk_store):
    state = build_system_state(
        copy_trade_service=copy_trade_service,
        audit_service=audit_service,
        signal_scanner=signal_scanner,
        telegram_control=telegram_control,
        telegram_bot=telegram_bot,
        desk_store=desk_store,
    )
    if state.status.value in {"halted", "degraded"}:
        message = "Configuracao invalida para execucao segura: " + " | ".join(state.reasons)
        raise RuntimeError(message)
    return state
