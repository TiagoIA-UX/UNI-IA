
# ================================================================
# Boitatá IA — Limpeza e Organização do Projeto
# Execute como: .\limpar_projeto.ps1
# ================================================================
 
$ROOT = "E:\UNI.IA"
 
Write-Host ""
Write-Host "Boitatá IA — Auditoria e Limpeza do Projeto" -ForegroundColor Cyan
Write-Host ""
 
$arquivos = @()
$arquivos += "$ROOT\fix_plataforma.ps1"
$arquivos += "$ROOT\Ler-Arquivos-Tarefa2.ps1"
$arquivos += "$ROOT\aplicar-tarefa1.ps1"
$arquivos += "$ROOT\APLICAR_WEBSOCKET.ps1"
$arquivos += "$ROOT\Analisar-Branches.ps1"
$arquivos += "$ROOT\consolidar_env.ps1"
$arquivos += "$ROOT\ai-sentinel\consolidar_env.ps1"
$arquivos += "$ROOT\script_legal_deploy.ps1"
$arquivos += "$ROOT\ai-sentinel\setup_mb.ps1"
$arquivos += "$ROOT\ai.js"
$arquivos += "$ROOT\data.js"
$arquivos += "$ROOT\engine.js"
$arquivos += "$ROOT\factors.js"
$arquivos += "$ROOT\patterns.js"
$arquivos += "$ROOT\app.js"
$arquivos += "$ROOT\index.html"
$arquivos += "$ROOT\run_backend.py"
$arquivos += "$ROOT\run_uni_ia.py"
$arquivos += "$ROOT\ai-sentinel\run_local_api.py"
$arquivos += "$ROOT\ai-sentinel\run_daily_report.py"
$arquivos += "$ROOT\ai-sentinel\run_risk_filter_aggregation.py"
$arquivos += "$ROOT\ai-sentinel\run_stress_test.py"
$arquivos += "$ROOT\ai-sentinel\run_backtest.py"
$arquivos += "$ROOT\zairyx-frontend\app\plataforma\start_system.ps1"
$arquivos += "$ROOT\ai-sentinel\public\index.html"
 
$pastas = @()
$pastas += "$ROOT\.pycache-temp"
$pastas += "$ROOT\ai-sentinel\stress_test_output"
$pastas += "$ROOT\ai-sentinel\stress_test_output_v2"
$pastas += "$ROOT\ai-sentinel\stress_test_output_v3"
$pastas += "$ROOT\ai-sentinel\stress_test_output_v4"
$pastas += "$ROOT\ai-sentinel\backtest_output_hardening"
$pastas += "$ROOT\ai-sentinel\frontend"
$pastas += "$ROOT\ai-sentinel\app"
$pastas += "$ROOT\ai-sentinel\zairyx-engine"
 
$moverDe = @()
$moverDe += "$ROOT\RELATORIO_COPTRADER.md"
$moverDe += "$ROOT\RELATORIO_DIA_05_05_2026.md"
$moverDe += "$ROOT\CHECKPOINT_UNI_IA_v1.0.md"
$moverDe += "$ROOT\RELEASE_NOTES_v1.0.0-alpha.md"
$moverDe += "$ROOT\healthcheck.ps1"
$moverDe += "$ROOT\start.ps1"
 
Write-Host "ARQUIVOS A DELETAR:" -ForegroundColor Red
foreach ($f in $arquivos) {
    if (Test-Path $f) { Write-Host "   $f" -ForegroundColor DarkRed }
}
 
Write-Host ""
Write-Host "PASTAS A DELETAR:" -ForegroundColor Red
foreach ($p in $pastas) {
    if (Test-Path $p) { Write-Host "   $p" -ForegroundColor DarkRed }
}
 
Write-Host ""
Write-Host "ARQUIVOS A MOVER PARA docs\relatorios:" -ForegroundColor Yellow
foreach ($f in $moverDe) {
    if (Test-Path $f) { Write-Host "   $f" -ForegroundColor DarkYellow }
}
 
Write-Host ""
$confirm = Read-Host "Confirma a limpeza? Digite SIM para continuar"
 
if ($confirm -ne "SIM") {
    Write-Host "Cancelado. Nenhum arquivo foi alterado." -ForegroundColor Yellow
    exit
}
 
Write-Host ""
Write-Host "Iniciando limpeza..." -ForegroundColor Green
 
$deletados = 0
$naoEncontrados = 0
 
foreach ($f in $arquivos) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "   OK: $(Split-Path $f -Leaf)" -ForegroundColor Green
        $deletados++
    } else {
        $naoEncontrados++
    }
}
 
foreach ($p in $pastas) {
    if (Test-Path $p) {
        Remove-Item $p -Recurse -Force
        Write-Host "   OK pasta: $(Split-Path $p -Leaf)" -ForegroundColor Green
        $deletados++
    } else {
        $naoEncontrados++
    }
}
 
Write-Host ""
Write-Host "Movendo para docs\relatorios..." -ForegroundColor Yellow
 
$destino = "$ROOT\docs\relatorios"
if (-not (Test-Path $destino)) {
    New-Item -ItemType Directory -Path $destino -Force | Out-Null
}
 
foreach ($f in $moverDe) {
    if (Test-Path $f) {
        Move-Item $f $destino -Force
        Write-Host "   OK movido: $(Split-Path $f -Leaf)" -ForegroundColor Yellow
    }
}
 
Write-Host ""
Write-Host "Limpando __pycache__..." -ForegroundColor Cyan
Get-ChildItem -Path "$ROOT\ai-sentinel" -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
    Write-Host "   OK: $($_.FullName)" -ForegroundColor DarkCyan
}
 
Write-Host ""
Write-Host "Limpeza concluida!" -ForegroundColor Green
Write-Host "   Removidos   : $deletados" -ForegroundColor Green
Write-Host "   Ja ausentes : $naoEncontrados" -ForegroundColor Gray
Write-Host ""
Write-Host "Para rodar o sistema:" -ForegroundColor Yellow
Write-Host "   cd E:\UNI.IA\ai-sentinel"
Write-Host "   .\venv\Scripts\Activate.ps1"
Write-Host "   cd E:\UNI.IA"
Write-Host "   python start_uni_ia.py"
Write-Host ""
 
