# Snapshot versionado para backup auditável (não inclui .env nem node_modules — não estão no Git).
$ErrorActionPreference = "Stop"
# win -> scripts -> boitata-doc -> raiz do monólito 01Boitata
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
if (-not (Test-Path (Join-Path $root ".git"))) {
    Write-Error "Execute a partir da raiz do repo; .git não encontrado em $root"
}
Push-Location $root
try {
    $dir = "E:\Boitata-backups"
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    $zip = Join-Path $dir ("01Boitata_git_archive_{0:yyyy-MM-dd}.zip" -f (Get-Date))
    git archive --format=zip -o $zip HEAD
    $hash = git rev-parse HEAD
    Write-Host "OK: $zip"
    Write-Host "HEAD: $hash"
}
finally {
    Pop-Location
}
