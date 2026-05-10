# ============================================================
#  UNI IA — LAUNCHER UNIFICADO v1.0
#  Salve como: E:\UNI.IA\start.ps1
#  Execute com: pwsh -ExecutionPolicy Bypass -File .\start.ps1
# ============================================================

$ROOT = "E:\UNI.IA"
$BACKEND = "$ROOT\ai-sentinel"
$FRONTEND = "$ROOT\zairyx-blog"
$API_URL = "http://127.0.0.1:8000"
$APP_URL = "http://localhost:3000/login"

# ─── Funções utilitárias ────────────────────────────────────

function Write-Step($n, $txt) {
    Write-Host "`n[$n] $txt" -ForegroundColor Cyan
}

function Wait-Port($url, $label, $maxSec = 30) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $maxSec) {
        try {
            Invoke-RestMethod -Uri $url -TimeoutSec 2 -ErrorAction Stop | Out-Null
            Write-Host "    ✅ $label pronto" -ForegroundColor Green
            return $true
        }
        catch { Start-Sleep -Milliseconds 800 }
    }
    Write-Host "    ❌ $label não respondeu em ${maxSec}s" -ForegroundColor Red
    return $false
}

# ─── HEADER ────────────────────────────────────────────────
Clear-Host
Write-Host @"
╔══════════════════════════════════════════════════╗
║          UNI IA — INICIALIZAÇÃO COMPLETA         ║
║     Backend · Frontend · Scanner · Browser       ║
╚══════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# ─── PASSO 1: Backend em janela separada (processo filho) ──
Write-Step "1/4" "Iniciando Backend (ai-sentinel :8000)..."

$backendCmd = @"
cd '$BACKEND'
& '$BACKEND\venv\Scripts\Activate.ps1'
python run_local_api.py
"@

Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $backendCmd
) -WindowStyle Normal

# ─── PASSO 2: Aguarda backend responder ────────────────────
Write-Step "2/4" "Aguardando backend ficar pronto..."
$backendOk = Wait-Port "$API_URL/api/desk/status" "Backend" 45

if (-not $backendOk) {
    Write-Host "`n  ERRO: Backend não iniciou. Verifique o venv e o .env.local." -ForegroundColor Red
    Write-Host "  Dica: abra manualmente o terminal do Backend e veja o erro." -ForegroundColor Yellow
    Read-Host "`nPressione Enter para sair"
    exit 1
}

# ─── PASSO 3: Frontend em janela separada ──────────────────
Write-Step "3/4" "Iniciando Frontend (zairyx-blog :3000)..."

$frontendCmd = @"
cd '$FRONTEND'
npm run dev
"@

Start-Process pwsh -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command", $frontendCmd
) -WindowStyle Normal

# Aguarda Next.js compilar (costuma levar 3–5s)
Write-Host "    Aguardando Next.js compilar..." -ForegroundColor Gray
Start-Sleep -Seconds 6

$frontendOk = Wait-Port "http://localhost:3000" "Frontend" 40

if (-not $frontendOk) {
    Write-Host "`n  AVISO: Frontend demorou mais que o esperado." -ForegroundColor Yellow
    Write-Host "  O navegador será aberto mesmo assim — atualize a página se necessário." -ForegroundColor Yellow
}

# ─── PASSO 4: Abre o navegador na tela de login ────────────
Write-Step "4/4" "Abrindo plataforma no navegador..."
Start-Process $APP_URL

# ─── STATUS FINAL ──────────────────────────────────────────
Write-Host "`n" 
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              ✅  PLATAFORMA NO AR                ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  🌐 Login    : http://localhost:3000/login       ║" -ForegroundColor White
Write-Host "║  ⚙️  Backend  : http://127.0.0.1:8000/docs       ║" -ForegroundColor White
Write-Host "║  📊 Sinais   : http://127.0.0.1:8000/api/signals/status  ║" -ForegroundColor White
Write-Host "╠══════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  Para encerrar: feche as janelas do Backend      ║" -ForegroundColor Gray
Write-Host "║  e do Frontend, ou pressione Ctrl+C em cada uma.║" -ForegroundColor Gray
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""