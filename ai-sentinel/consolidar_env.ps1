# ============================================================
#  UNI IA — Consolidacao do .env.local unico na raiz
#  Execute com: pwsh -ExecutionPolicy Bypass -File E:\UNI.IA\consolidar_env.ps1
#  
#  O que este script faz:
#  1. Faz backup de todos os .env.local existentes
#  2. Grava o .env.local consolidado e limpo na raiz
#  3. Cria symlinks nos subprojetos apontando para a raiz
#  4. Blinda o .gitignore em todos os niveis
#  5. Valida tudo no final
#
#  ATENCAO: Apos rodar, revogue e substitua TODAS as chaves
#  listadas na sessao de alerta de seguranca.
# ============================================================

$ROOT     = "E:\UNI.IA"
$BACKUP   = "$ROOT\.secrets-backup"
$TS       = Get-Date -Format "yyyyMMdd_HHmmss"
$PASS     = "[OK]"
$FAIL     = "[ERRO]"
$WARN     = "[AVISO]"

function Write-Header($txt) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  $txt" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

# ─── 1. BACKUP ────────────────────────────────────────────────────────────────
Write-Header "1. BACKUP DE SEGURANCA"

New-Item -ItemType Directory -Force -Path $BACKUP | Out-Null

$envFiles = @(
    "$ROOT\.env.local",
    "$ROOT\ai-sentinel\.env.local",
    "$ROOT\zairyx-frontend\.env.local"
)

foreach ($f in $envFiles) {
    if (Test-Path $f) {
        $dest = "$BACKUP\" + ($f.Replace("$ROOT\","").Replace("\","-")) + ".$TS.bak"
        Copy-Item $f $dest
        Write-Host "$PASS Backup: $dest" -ForegroundColor Green
    }
}

# ─── 2. .env.local CONSOLIDADO E LIMPO ───────────────────────────────────────
Write-Header "2. GRAVANDO .env.local CONSOLIDADO NA RAIZ"

# ATENCAO: Todas as chaves abaixo marcadas com REVOGAR_E_SUBSTITUIR
# devem ser substituidas por novas chaves apos revogar as antigas.
# Veja o checklist no final do script.

$envConsolidado = @"
# ================================================================
#  UNI IA — VARIAVEIS DE AMBIENTE UNIFICADAS
#  Arquivo unico e fonte da verdade para todo o projeto.
#  Subprojetos (ai-sentinel, zairyx-frontend) leem via symlink.
#
#  STATUS DE SEGURANCA: PENDENTE REVOGACAO
#  Todas as chaves marcadas com [REVOGAR] devem ser substituidas.
#  Veja: docs/governance/environment-checklist.md
#
#  Ultima atualizacao: $TS
#  Responsavel: Fundador UNI IA
# ================================================================

# ── MODO OPERACIONAL ─────────────────────────────────────────────
# paper = nunca executa ordem real
# live  = executa ordens reais (exige DESK_REQUIRE_MANUAL_APPROVAL=true)
DESK_MODE=paper
DESK_REQUIRE_MANUAL_APPROVAL=true
DESK_MIN_SCORE=75
DESK_ALLOWED_ASSETS=BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,LTCUSDT
DESK_STORE_TIMEOUT_SECONDS=10

# ── BROKER PRINCIPAL: MERCADO BITCOIN ───────────────────────────
# Troque para "bybit" se quiser usar a Bybit em paper
BROKER_PROVIDER=mercadobitcoin
BROKER_API_BASE_URL=https://www.mercadobitcoin.com.br
BROKER_API_KEY=REVOGAR_E_SUBSTITUIR_MB_API_KEY
BROKER_API_SECRET=REVOGAR_E_SUBSTITUIR_MB_API_SECRET
BROKER_TIMEOUT_SECONDS=10
MB_DEFAULT_QTY=0.0001
MB_TRADE_START_HOUR=9
MB_TRADE_END_HOUR=22
MB_ORDER_TIMEOUT_HOURS=4

# ── BROKER SECUNDARIO: BYBIT (paper/analise apenas) ─────────────
# Usado apenas para dados de mercado e analise tecnica
# NAO usado para execucao enquanto BROKER_PROVIDER=mercadobitcoin
BYBIT_API_BASE_URL=https://api.bybit.com
BYBIT_API_KEY=REVOGAR_E_SUBSTITUIR_BYBIT_KEY
BYBIT_API_SECRET=REVOGAR_E_SUBSTITUIR_BYBIT_SECRET
BYBIT_RECV_WINDOW=5000
BYBIT_CATEGORY=linear
BYBIT_DEFAULT_QTY=0.001
BYBIT_SIGNAL_ASSETS=BTCUSDT,ETHUSDT,SOLUSDT
BYBIT_SIGNAL_INTERVAL=15m
NEXT_PUBLIC_BYBIT_SIGNAL_ASSETS=BTCUSDT,ETHUSDT,SOLUSDT

# ── COPY TRADE ──────────────────────────────────────────────────
COPY_TRADE_ENABLED=false
COPY_TRADE_MIN_CONFIDENCE=75
COPY_TRADE_MAX_RISK_PERCENT=1.0

# ── ATR STOP LOSS ───────────────────────────────────────────────
ATR_SL_ENABLED=true
ATR_SL_MULTIPLIER=1.5
ATR_SL_PERIOD=14

# ── SUPABASE (BANCO DE DADOS) ────────────────────────────────────
NEXT_PUBLIC_SUPABASE_URL=https://fgwyinfkjjgdrcfyiguu.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=REVOGAR_E_SUBSTITUIR_SUPABASE_ANON
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=REVOGAR_E_SUBSTITUIR_SUPABASE_ANON
SUPABASE_SERVICE_ROLE_KEY=REVOGAR_E_SUBSTITUIR_SUPABASE_SERVICE_ROLE

# ── GROQ API (MOTOR DE IA) ───────────────────────────────────────
GROQ_API_KEY=REVOGAR_E_SUBSTITUIR_GROQ_KEY
GROQ_MODEL=llama-3.1-8b-instant
GROQ_FORCE_JSON_MODE=true

# ── TELEGRAM BOTS ───────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=REVOGAR_E_SUBSTITUIR_BOT_TOKEN
TELEGRAM_FREE_CHANNEL=@uni_ia_free_bot
TELEGRAM_PREMIUM_CHANNEL=@uni_ia_premium_bot
TELEGRAM_FREE_BOT_USERNAME=uni_ia_free_bot
TELEGRAM_PREMIUM_BOT_USERNAME=uni_ia_premium_bot
TELEGRAM_FREE_BOT_TOKEN=REVOGAR_E_SUBSTITUIR_FREE_BOT_TOKEN
TELEGRAM_PREMIUM_BOT_TOKEN=REVOGAR_E_SUBSTITUIR_PREMIUM_BOT_TOKEN
TELEGRAM_TIMEOUT_SECONDS=10
TELEGRAM_MAX_RETRIES=3

# ── TELEGRAM ADMIN ──────────────────────────────────────────────
TELEGRAM_CONTROL_ENABLED=true
TELEGRAM_ADMIN_CHAT_IDS=PREENCHER_SEU_CHAT_ID
TELEGRAM_ADMIN_USER_IDS=PREENCHER_SEU_USER_ID
TELEGRAM_POLL_TIMEOUT_SECONDS=30
LLM_FAILURE_ALERT_ENABLED=true

# ── RESEND EMAILS ───────────────────────────────────────────────
RESEND_API_KEY=REVOGAR_E_SUBSTITUIR_RESEND_KEY

# ── VERCEL ──────────────────────────────────────────────────────
VERCEL_TOKEN=REVOGAR_E_SUBSTITUIR_VERCEL_TOKEN

# ── CRON JOB ────────────────────────────────────────────────────
# Gere novo com: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
CRON_SECRET=GERAR_NOVO_COM_COMANDO_ACIMA

# ── GOOGLE OAUTH ────────────────────────────────────────────────
GOOGLE_CLIENT_ID=REVOGAR_E_SUBSTITUIR_GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET=REVOGAR_E_SUBSTITUIR_GOOGLE_CLIENT_SECRET

# ── UNI IA API (LOCAL) ──────────────────────────────────────────
UNI_IA_API_HOST=127.0.0.1
UNI_IA_API_PORT=8000
UNI_IA_MODEL_VERSION=v1

# ── SIGNAL SCANNER ──────────────────────────────────────────────
SIGNAL_SCANNER_ENABLED=false
SIGNAL_SCAN_ASSETS=BTCUSDT,ETHUSDT,SOLUSDT
SIGNAL_ALLOWED_CLASSIFICATIONS=OPORTUNIDADE
SIGNAL_MIN_SCORE=75
SIGNAL_SCAN_INTERVAL_SECONDS=60
SIGNAL_SCAN_STAGGER_SECONDS=2
SIGNAL_DEDUPE_TTL_SECONDS=300
SIGNAL_RECENT_LIMIT=20
SIGNAL_SESSION_FILTER_ENABLED=false
SIGNAL_DISPATCH_LOG_PATH=ai-sentinel/runtime_logs/signal_dispatch.jsonl

# ── KILL SWITCH ─────────────────────────────────────────────────
KILL_SWITCH_ENABLED=true
KILL_SWITCH_MAX_DAILY_LOSS_PCT=3.0
KILL_SWITCH_MAX_DRAWDOWN_PCT=10.0
KILL_SWITCH_WINDOW_DAYS=1
KILL_SWITCH_SAMPLE_LIMIT=5000
KILL_SWITCH_LOG_PATH=ai-sentinel/runtime_logs/risk_events.jsonl

# ── AUDITORIA E LOGS ─────────────────────────────────────────────
AUDIT_TABLE_NAME=uni_ia_operational_audit
AUDIT_TIMEOUT_SECONDS=10
AUDIT_EVENT_VARIANT=A
AUDIT_EVENT_PAGE=ai-sentinel-operational
AUDIT_EVENT_LOCALE=pt-BR
FEATURE_STORE_LOG_PATH=ai-sentinel/runtime_logs/feature_store.jsonl
FEEDBACK_LOG_PATH=ai-sentinel/runtime_logs/feedback.jsonl
FEEDBACK_STORE_TIMEOUT_SECONDS=10
OUTCOME_LOG_PATH=ai-sentinel/runtime_logs/outcomes.jsonl
OUTCOME_TRACKER_TIMEOUT_SECONDS=10

# ── STRATEGY E AGENTES ──────────────────────────────────────────
STRATEGY_DEFAULT_MODE=swing
AEGIS_ENABLE_DYNAMIC_RECALIBRATION=false
AEGIS_RECALIBRATION_WINDOW_DAYS=90
AEGIS_RECALIBRATION_MIN_SAMPLES=5

# ── BACKTEST ────────────────────────────────────────────────────
BACKTEST_ASSET=BTCUSDT
BACKTEST_INITIAL_CAPITAL=10000
BACKTEST_FEE_RATE=0.0006
BACKTEST_SLIPPAGE_BPS=3
BACKTEST_SPREAD_BPS=1
BACKTEST_RISK_PER_TRADE_PCT=1.0
BACKTEST_MAX_DRAWDOWN_PCT_LIMIT=20
BACKTEST_FAST_SMA_PERIOD=5
BACKTEST_SLOW_SMA_PERIOD=20
BACKTEST_ATR_PERIOD=14
BACKTEST_ATR_MULTIPLIER=1.5
BACKTEST_MIN_SCORE=70
BACKTEST_MIN_ATR_PCT=0.002
BACKTEST_TAKE_PROFIT_RR=2.0

# ── CORS ────────────────────────────────────────────────────────
ALLOWED_ORIGINS=https://zairyx.ai,https://www.zairyx.ai

# ── MT5 (LEGADO — NAO USAR EM PRODUCAO COM MB) ──────────────────
# Mantido apenas para referencia historica do backtest de gaps
# MT5_LOGIN=106689044
# MT5_PASSWORD=REVOGAR_NAO_USAR_EM_PRODUCAO
# MT5_SERVER=MetaQuotes-Demo
"@

Set-Content -Path "$ROOT\.env.local" -Value $envConsolidado -Encoding UTF8
Write-Host "$PASS .env.local consolidado gravado em $ROOT" -ForegroundColor Green

# ─── 3. SYMLINKS NOS SUBPROJETOS ─────────────────────────────────────────────
Write-Header "3. CRIANDO SYMLINKS NOS SUBPROJETOS"

# Remove os .env.local antigos dos subprojetos e cria symlinks
$subprojects = @(
    "$ROOT\ai-sentinel",
    "$ROOT\zairyx-frontend"
)

foreach ($sp in $subprojects) {
    $envPath = "$sp\.env.local"
    if (Test-Path $envPath) {
        Remove-Item $envPath -Force
        Write-Host "$PASS Removido: $envPath" -ForegroundColor Green
    }
    try {
        New-Item -ItemType SymbolicLink -Path $envPath -Target "$ROOT\.env.local" -ErrorAction Stop | Out-Null
        Write-Host "$PASS Symlink criado: $envPath -> $ROOT\.env.local" -ForegroundColor Green
    } catch {
        # Fallback: copia o arquivo se symlink falhar (sem permissao admin)
        Copy-Item "$ROOT\.env.local" $envPath
        Write-Host "$WARN Symlink falhou, usando copia: $envPath (rode como Admin para symlinks)" -ForegroundColor Yellow
    }
}

# ─── 4. .gitignore BLINDADO ──────────────────────────────────────────────────
Write-Header "4. BLINDANDO .gitignore EM TODOS OS NIVEIS"

$gitignoreEntry = @"

# === UNI IA SEGURANCA — NAO REMOVER ===
.env.local
.env*.local
.env.production
.secrets-backup/
*.bak
"@

$gitignoreTargets = @(
    "$ROOT\.gitignore",
    "$ROOT\ai-sentinel\.gitignore",
    "$ROOT\zairyx-frontend\.gitignore"
)

foreach ($gi in $gitignoreTargets) {
    if (Test-Path $gi) {
        $content = Get-Content $gi -Raw
        if ($content -notmatch "\.env\.local") {
            Add-Content -Path $gi -Value $gitignoreEntry -Encoding UTF8
            Write-Host "$PASS .gitignore atualizado: $gi" -ForegroundColor Green
        } else {
            Write-Host "$WARN .env.local ja esta no .gitignore: $gi" -ForegroundColor Yellow
        }
    } else {
        Set-Content -Path $gi -Value $gitignoreEntry -Encoding UTF8
        Write-Host "$PASS .gitignore criado: $gi" -ForegroundColor Green
    }
}

# ─── 5. CHECKLIST DE REVOGACAO ───────────────────────────────────────────────
Write-Header "5. CHECKLIST DE REVOGACAO DE CHAVES"

$checklist = @"
# ================================================================
#  UNI IA — CHECKLIST DE REVOGACAO DE CREDENCIAIS
#  Gerado em: $TS
#  Arquivo: $ROOT\docs\governance\environment-checklist.md
# ================================================================

## STATUS: PENDENTE — Revogue TODAS as chaves abaixo

### Credenciais a revogar e regenerar

| Servico | Onde revogar | Status |
|---|---|---|
| GROQ_API_KEY | console.groq.com → API Keys → Delete | [ ] |
| VERCEL_TOKEN | vercel.com → Settings → Tokens → Delete | [ ] |
| TELEGRAM_BOT_TOKEN | @BotFather → /revoke | [ ] |
| TELEGRAM_FREE_BOT_TOKEN | @BotFather → /revoke | [ ] |
| TELEGRAM_PREMIUM_BOT_TOKEN | @BotFather → /revoke | [ ] |
| RESEND_API_KEY | resend.com → API Keys → Delete | [ ] |
| BYBIT_API_KEY | bybit.com → API Management → Delete | [ ] |
| SUPABASE_SERVICE_ROLE_KEY | supabase.com → Settings → API → Regenerate | [ ] |
| SUPABASE_ANON_KEY | supabase.com → Settings → API → Regenerate | [ ] |
| GOOGLE_CLIENT_SECRET | console.cloud.google.com → Credentials → Regenerate | [ ] |
| CRON_SECRET | Gerar novo: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))" | [ ] |
| GOOGLE_ADMIN_PASSWORD | myaccount.google.com → Seguranca → Alterar senha | [ ] |

### Apos revogar

1. Gere as novas chaves em cada servico
2. Abra E:\UNI.IA\.env.local
3. Substitua cada valor REVOGAR_E_SUBSTITUIR_* pela nova chave
4. Salve o arquivo
5. Reinicie o backend: python run_local_api.py
6. Marque cada item acima como [x]

### Observacoes de seguranca

- O .env.local NUNCA deve ser commitado no GitHub
- O .gitignore ja esta configurado para bloquear
- As chaves do MT5 foram comentadas — MT5 nao sera usado com MB ativo
- COPY_TRADE_ENABLED=false ate as chaves do MB estarem configuradas
- DESK_MODE=paper ate validacao completa em paper por 7+ dias
"@

New-Item -ItemType Directory -Force -Path "$ROOT\docs\governance" | Out-Null
Set-Content -Path "$ROOT\docs\governance\environment-checklist.md" -Value $checklist -Encoding UTF8
Write-Host "$PASS Checklist gravado em docs\governance\environment-checklist.md" -ForegroundColor Green

# ─── 6. VALIDACAO FINAL ──────────────────────────────────────────────────────
Write-Header "6. VALIDACAO FINAL"

# Verifica .env.local na raiz
if (Test-Path "$ROOT\.env.local") {
    $lines = (Get-Content "$ROOT\.env.local").Count
    Write-Host "$PASS .env.local raiz: $lines linhas" -ForegroundColor Green
} else {
    Write-Host "$FAIL .env.local raiz NAO encontrado" -ForegroundColor Red
}

# Verifica symlinks
foreach ($sp in $subprojects) {
    $envPath = "$sp\.env.local"
    if (Test-Path $envPath) {
        $item = Get-Item $envPath
        if ($item.LinkType -eq "SymbolicLink") {
            Write-Host "$PASS Symlink OK: $envPath" -ForegroundColor Green
        } else {
            Write-Host "$WARN Copia (nao symlink): $envPath — funciona mas nao e ideal" -ForegroundColor Yellow
        }
    } else {
        Write-Host "$FAIL Nao encontrado: $envPath" -ForegroundColor Red
    }
}

# Verifica .gitignore
foreach ($gi in $gitignoreTargets) {
    if (Test-Path $gi) {
        $check = Select-String -Path $gi -Pattern "\.env\.local" -Quiet
        if ($check) {
            Write-Host "$PASS .gitignore protege .env.local: $gi" -ForegroundColor Green
        } else {
            Write-Host "$FAIL .env.local NAO protegido: $gi" -ForegroundColor Red
        }
    }
}

# Verifica se chaves antigas ainda estao no Git index
$gitCheck = git -C $ROOT ls-files --error-unmatch ".env.local" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "$FAIL CRITICO: .env.local esta rastreado pelo Git!" -ForegroundColor Red
    Write-Host "   Execute: git -C $ROOT rm --cached .env.local" -ForegroundColor Yellow
    Write-Host "   Execute: git -C $ROOT rm --cached ai-sentinel/.env.local" -ForegroundColor Yellow
    Write-Host "   Execute: git -C $ROOT rm --cached zairyx-frontend/.env.local" -ForegroundColor Yellow
} else {
    Write-Host "$PASS .env.local NAO rastreado pelo Git" -ForegroundColor Green
}

# ─── RESUMO FINAL ────────────────────────────────────────────────────────────
Write-Header "RESUMO"
Write-Host ""
Write-Host "  Estrutura final:" -ForegroundColor White
Write-Host "  E:\UNI.IA\.env.local          <- FONTE DA VERDADE" -ForegroundColor Cyan
Write-Host "  E:\UNI.IA\ai-sentinel\.env.local    <- symlink para raiz" -ForegroundColor Cyan
Write-Host "  E:\UNI.IA\zairyx-frontend\.env.local <- symlink para raiz" -ForegroundColor Cyan
Write-Host ""
Write-Host "  PROXIMO PASSO OBRIGATORIO:" -ForegroundColor Yellow
Write-Host "  1. Revogue TODAS as chaves (veja docs\governance\environment-checklist.md)" -ForegroundColor Yellow
Write-Host "  2. Substitua os valores REVOGAR_E_SUBSTITUIR_* no .env.local" -ForegroundColor Yellow
Write-Host "  3. Coloque as chaves reais do Mercado Bitcoin:" -ForegroundColor Yellow
Write-Host "     BROKER_API_KEY=sua_chave_mb" -ForegroundColor Cyan
Write-Host "     BROKER_API_SECRET=seu_secret_mb" -ForegroundColor Cyan
Write-Host "  4. Rode o healthcheck: pwsh -File E:\UNI.IA\healthcheck.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Backup dos arquivos originais em: $BACKUP" -ForegroundColor Gray
Write-Host ""