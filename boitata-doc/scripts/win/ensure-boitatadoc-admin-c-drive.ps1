# Cria C:\BoitataDOC\data e tenta garantir permissões de escrita ao utilizador atual.
# Se o Windows Defender / política impedir escrita na raiz de C:, use outro caminho e defina DOC_LEDGER_PATH.

$ErrorActionPreference = "Stop"

$base = 'C:\BoitataDOC'
$data = Join-Path $base 'data'
New-Item -ItemType Directory -Force -Path $data | Out-Null

$principal = "$env:USERDOMAIN\$env:USERNAME"

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator
)

Write-Host "Pasta: $data"
Write-Host "Utilizador: $principal  (Administrador=$isAdmin)"

if ($isAdmin) {
    & icacls.exe $base /grant:r "${principal}:(OI)(CI)M" /T | Out-Host
    Write-Host 'icacls aplicado sob elevacao.'
}
else {
    Write-Host 'Dica: se escrever em C:\ falhar com "acesso negado", execute este script como Administrador ou defina DOC_LEDGER_PATH para um diretório dentro do seu perfil.'
}

$p = Join-Path $data 'doc_ledger.jsonl'
Write-Host ""
Write-Host "Sugestão .env.local (ai-sentinel):" 
Write-Host "DOC_LEDGER_ENABLED=true"
Write-Host "DOC_LEDGER_PATH=$p"
