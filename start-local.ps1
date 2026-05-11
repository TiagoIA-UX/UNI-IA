# Boitatá — liga motor (ai-sentinel) + site (Next) em casa, grátis.
# Uso: PowerShell na raiz do repo: .\start-local.ps1
# Requer: Node instalado; Python + venv em .\.venv (ou python no PATH).

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
  Write-Host "AVISO: nao achei .venv\Scripts\python.exe — uso 'python' do PATH." -ForegroundColor Yellow
  $Py = "python"
}

$Api = Join-Path $Root "ai-sentinel"
$Web = Join-Path $Root "zairyx-frontend"

if (-not (Test-Path $Api)) { throw "Pasta nao encontrada: $Api" }
if (-not (Test-Path $Web)) { throw "Pasta nao encontrada: $Web" }

Write-Host "A abrir 2 janelas: API :8000 | Next :3000" -ForegroundColor Cyan

# Motor FastAPI (janela 1)
$cmdApi = "title Boitatá API && cd /d `"$Api`" && `"$Py`" -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --http h11"
Start-Process cmd.exe -ArgumentList @("/k", $cmdApi) -WindowStyle Normal

Start-Sleep -Seconds 2

# Frontend Next (janela 2)
$cmdWeb = "title Boitatá Web && cd /d `"$Web`" && npm run dev"
Start-Process cmd.exe -ArgumentList @("/k", $cmdWeb) -WindowStyle Normal

Write-Host ""
Write-Host "Quando aparecer 'Ready' no Next: http://localhost:3000" -ForegroundColor Green
Write-Host "Documentacao API: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "Fecha cada janela CMD com exit ou a cruz para desligar." -ForegroundColor DarkGray
