# ============================================================
#  UNI IA — DIAGNÓSTICO COMPLETO v1.2
#  Execute com: pwsh -ExecutionPolicy Bypass -File .\healthcheck.ps1
#  ou cole direto no PowerShell 7+
# ============================================================

$BASE_URL = "http://127.0.0.1:8000"
$FRONT_URL = "http://localhost:3000"
$ASSETS = @("BTCUSDT", "ETHUSDT", "SOLUSDT")
$PASS = "[OK]"
$FAIL = "[FALHOU]"
$WARN = "[AVISO]"

function Write-Header($txt) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  $txt" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

function Test-Endpoint($label, $url, $expectKey = $null) {
    try {
        $r = Invoke-RestMethod -Uri $url -TimeoutSec 5 -ErrorAction Stop
        if ($expectKey -and -not ($r.PSObject.Properties.Name -contains $expectKey)) {
            Write-Host "$WARN $label — resposta sem campo '$expectKey'" -ForegroundColor Yellow
            return $null
        }
        Write-Host "$PASS $label" -ForegroundColor Green
        return $r
    }
    catch {
        Write-Host "$FAIL $label — $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# ─── 1. BACKEND ────────────────────────────────────────────
Write-Header "1. BACKEND (ai-sentinel :8000)"

$desk = Test-Endpoint "Desk status"      "$BASE_URL/api/desk/status"   "mode"
$sig = Test-Endpoint "Scanner status"   "$BASE_URL/api/signals/status" "enabled"
$tg = Test-Endpoint "Telegram status"  "$BASE_URL/api/telegram/status"

if ($desk) {
    Write-Host "   Modo atual : $($desk.mode)" -ForegroundColor White
    Write-Host "   Aprovação  : $($desk.require_manual_approval)" -ForegroundColor White
}
if ($sig) {
    $scanState = if ($sig.enabled) { "ATIVO" } else { "PARADO" }
    Write-Host "   Scanner    : $scanState" -ForegroundColor $(if ($sig.enabled) { "Green" } else { "Yellow" })
}

# ─── 2. FRONTEND ───────────────────────────────────────────
Write-Header "2. FRONTEND (zairyx-blog :3000)"

try {
    $fr = Invoke-WebRequest -Uri $FRONT_URL -TimeoutSec 5 -UseBasicParsing
    if ($fr.StatusCode -eq 200) {
        Write-Host "$PASS Frontend respondendo (HTTP $($fr.StatusCode))" -ForegroundColor Green
    }
}
catch {
    Write-Host "$FAIL Frontend inacessível — rode: cd zairyx-blog && npm run dev" -ForegroundColor Red
}

# ─── 3. BYBIT LIVE FEED ────────────────────────────────────
Write-Header "3. BYBIT LIVE FEED (candles em tempo real)"

$bybitOk = 0
foreach ($asset in $ASSETS) {
    try {
        $url = "$BASE_URL/api/bybit/signals"
        $r = Invoke-RestMethod -Uri $url -TimeoutSec 8 -ErrorAction Stop
        # Tenta campo do asset específico ou array
        $found = $false
        if ($r.PSObject.Properties.Name -contains $asset) { $found = $true }
        elseif ($r -is [System.Array] -and $r.Count -gt 0) { $found = $true }

        if ($found) {
            Write-Host "$PASS $asset — feed recebido" -ForegroundColor Green
            $bybitOk++
        }
        else {
            Write-Host "$WARN $asset — sem dado no payload" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "$FAIL $asset — $($_.Exception.Message)" -ForegroundColor Red
    }
}
Write-Host "   Bybit feeds OK: $bybitOk / $($ASSETS.Count)" -ForegroundColor $(if ($bybitOk -eq $ASSETS.Count) { "Green" } else { "Yellow" })

# ─── 4. ANÁLISE DE AGENTES (1 ativo de teste) ──────────────
Write-Header "4. AGENTES IA (análise de teste — BTCUSDT)"

try {
    $body = @{ mode = "paper" } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$BASE_URL/api/analyze/BTCUSDT" `
        -Method POST -Body $body -ContentType "application/json" `
        -TimeoutSec 30 -ErrorAction Stop

    $agents = @("macro", "atlas", "orion", "news", "sentiment", "trends", "fundamentalist", "aegis")
    $found = @()
    $miss = @()

    foreach ($ag in $agents) {
        # Busca case-insensitive no objeto retornado
        $keys = $r.PSObject.Properties.Name | Where-Object { $_ -imatch $ag }
        if ($keys) { $found += $ag } else { $miss += $ag }
    }

    Write-Host "$PASS Análise retornou resposta" -ForegroundColor Green
    Write-Host "   Score      : $($r.score)"          -ForegroundColor White
    Write-Host "   Classificação: $($r.classification)" -ForegroundColor White
    Write-Host "   Confiança  : $($r.confidence)%"    -ForegroundColor White
    Write-Host "   Agentes detectados: $($found -join ', ')" -ForegroundColor Green
    if ($miss.Count -gt 0) {
        Write-Host "   Agentes ausentes  : $($miss -join ', ')" -ForegroundColor Yellow
    }

}
catch {
    Write-Host "$FAIL Análise falhou — $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Dica: verifique GROQ_API_KEY no .env.local e se o venv está ativo" -ForegroundColor Yellow
}

# ─── 5. FILA MULTI-TENANT (desk pending) ───────────────────
Write-Header "5. MESA MULTI-TENANT (fila de aprovação)"

$pending = Test-Endpoint "Fila de pendências" "$BASE_URL/api/desk/pending"
if ($pending -ne $null) {
    $count = if ($pending -is [System.Array]) { $pending.Count } else { 0 }
    Write-Host "   Pendências na fila: $count" -ForegroundColor White
    if ($count -gt 0) {
        $pending | Select-Object -First 3 | ForEach-Object {
            Write-Host "   • $($_.request_id) | $($_.asset) | score=$($_.score)" -ForegroundColor Cyan
        }
    }
}

# ─── 6. AUDITORIA RÁPIDA ───────────────────────────────────
Write-Header "6. LOGS DE AUDITORIA (últimas entradas)"

$logPaths = @(
    "ai-sentinel\runtime_logs\signal_dispatch.jsonl",
    "ai-sentinel\runtime_logs\risk_events.jsonl",
    "ai-sentinel\runtime_logs\feedback.jsonl"
)

foreach ($lp in $logPaths) {
    if (Test-Path $lp) {
        $lines = Get-Content $lp -Tail 1 -ErrorAction SilentlyContinue
        Write-Host "$PASS $lp — última entrada: $lines" -ForegroundColor Green
    }
    else {
        Write-Host "$WARN $lp não existe ainda (normal se scanner nunca rodou)" -ForegroundColor Yellow
    }
}

# ─── 7. CICLO RÁPIDO (opcional) ────────────────────────────
Write-Header "7. DISPARAR CICLO DE VARREDURA AGORA?"

$resp = Read-Host "Deseja executar /api/signals/run-cycle agora? (s/N)"
if ($resp -imatch "^s") {
    try {
        $r = Invoke-RestMethod -Uri "$BASE_URL/api/signals/run-cycle" -Method POST -TimeoutSec 60
        Write-Host "$PASS Ciclo executado. Resultado:" -ForegroundColor Green
        $r | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Cyan
    }
    catch {
        Write-Host "$FAIL Ciclo falhou — $($_.Exception.Message)" -ForegroundColor Red
    }
}
else {
    Write-Host "   Pulado." -ForegroundColor Gray
}

# ─── RESUMO FINAL ──────────────────────────────────────────
Write-Header "RESUMO"
Write-Host "  Backend   : $BASE_URL/docs  (Swagger UI)" -ForegroundColor White
Write-Host "  Frontend  : $FRONT_URL" -ForegroundColor White
Write-Host "  Bybit feed: $BASE_URL/api/bybit/signals" -ForegroundColor White
Write-Host "  Auditoria : $BASE_URL/api/desk/status" -ForegroundColor White
Write-Host "`n  Se algo falhou, verifique:" -ForegroundColor Yellow
Write-Host "  1. venv ativo no ai-sentinel (source venv/Scripts/activate)" -ForegroundColor Yellow
Write-Host "  2. .env.local com GROQ_API_KEY, BYBIT_SIGNAL_ASSETS e DESK_MODE" -ForegroundColor Yellow
Write-Host "  3. python run_local_api.py rodando no Terminal 1" -ForegroundColor Yellow
Write-Host "  4. npm run dev rodando no Terminal 2 (pasta zairyx-blog)" -ForegroundColor Yellow
Write-Host "`n  Telegram admin: /cycle para forçar varredura manual" -ForegroundColor Cyan
Write-Host ""