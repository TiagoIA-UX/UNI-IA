Write-Host "--- INICIANDO BOITATÁ IA: ORQUESTRAÇÃO DE AUDITORIA ---" -ForegroundColor Cyan

# 1. Liberar políticas de execução
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# 2. Iniciar o Backend (FastAPI) em background
Write-Host "[1/2] Ativando Ambiente Virtual e Backend..." -ForegroundColor Yellow
$BackendJob = Start-Process python -ArgumentList "-m api.main" `
    -WorkingDirectory "E:\UNI.IA\ai-sentinel" `
    -PassThru -WindowStyle Normal # Mude para 'Hidden' se não quiser ver a janela extra

# 3. Aguardar o Backend estabilizar (5 segundos)
Start-Sleep -Seconds 5

# 4. Iniciar o Frontend (Next.js)
Write-Host "[2/2] Subindo Interface do Dashboard..." -ForegroundColor Yellow
Write-Host "Acesse: http://localhost:3000/plataforma" -ForegroundColor Green

cd "E:\UNI.IA\zairyx-frontend"
npm run dev