# Script para verificar Docker e fazer scan com Docker Scout

Write-Host "=== Verificando Docker ===" -ForegroundColor Cyan
docker version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker nao esta instalado!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Docker Scout disponivel ===" -ForegroundColor Cyan
docker scout version

Write-Host "`n=== Construindo imagem Docker ===" -ForegroundColor Cyan
docker build -t comandas_api:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erro ao construir imagem!" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Escaneando vulnerabilidades com Docker Scout ===" -ForegroundColor Cyan
docker scout cves comandas_api:latest

Write-Host "`n=== Vulnerabilidades apenas ALTAS ===" -ForegroundColor Cyan
docker scout cves --severity high comandas_api:latest

Write-Host "`n=== Recomendacoes de seguranca ===" -ForegroundColor Cyan
docker scout recommendations comandas_api:latest

Write-Host "`n[OK] Scan completo!" -ForegroundColor Green
