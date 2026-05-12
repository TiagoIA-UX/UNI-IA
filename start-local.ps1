# start-local.ps1 - Boitata IA
# Uso: clique duplo em start-local.cmd ou: powershell -File start-local.ps1
# Compativel com Windows PowerShell 5.1 e PowerShell 7+

$Root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api     = Join-Path $Root "ai-sentinel"
$Web     = Join-Path $Root "zairyx-frontend"
$Venv    = Join-Path $Root "venv"
$VenvDot = Join-Path $Root ".venv"
$VenvAi  = Join-Path $Api "venv"
$ApiPort = 8010
$ApiUrl  = "http://127.0.0.1:$ApiPort"

# Python: .venv raiz > venv raiz > venv ai-sentinel > PATH
if (Test-Path (Join-Path $VenvDot "Scripts\python.exe")) {
    $Py = Join-Path $VenvDot "Scripts\python.exe"
} elseif (Test-Path (Join-Path $Venv "Scripts\python.exe")) {
    $Py = Join-Path $Venv "Scripts\python.exe"
} elseif (Test-Path (Join-Path $VenvAi "Scripts\python.exe")) {
    $Py = Join-Path $VenvAi "Scripts\python.exe"
} else {
    $Py = "python"
}

Write-Host ""
Write-Host "Boitata IA - iniciando..." -ForegroundColor Cyan
Write-Host "  API  : $Api" -ForegroundColor DarkGray
Write-Host "  Web  : $Web" -ForegroundColor DarkGray
Write-Host "  Python: $Py" -ForegroundColor DarkGray
Write-Host ""

# Terminal 1 - API (porta 8010 evita conflito com outro processo na 8000)
Start-Process cmd.exe -ArgumentList @(
    "/k",
    "title Boitata-API & cd /d `"$Api`" & `"$Py`" -m uvicorn api.main:app --host 127.0.0.1 --port $ApiPort --http h11"
)

Start-Sleep -Seconds 3

# Terminal 2 - Next aponta para a mesma API nesta sessao (nao precisa editar .env)
$webCmd = "title Boitata-Web & cd /d `"$Web`" & set NEXT_PUBLIC_AI_API_URL=$ApiUrl& set NEXT_PUBLIC_API_BASE=$ApiUrl& npm run dev"
Start-Process cmd.exe -ArgumentList @("/k", $webCmd)

Write-Host "Dois terminais abertos." -ForegroundColor Green
Write-Host "  API : $ApiUrl/docs" -ForegroundColor White
Write-Host "  Site: http://localhost:3000/plataforma" -ForegroundColor White
Write-Host ""
Write-Host "Para parar: feche cada janela CMD." -ForegroundColor DarkGray
