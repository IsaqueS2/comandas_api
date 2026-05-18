# Script para fazer push da imagem Docker

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "latest"
)

$projectRoot = "c:\Users\isaque.santos\Documents\Desenvolvimento Web\Comandas_api\comandas_api"
$imageName = "comandas_api"

Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "DOCKER PUSH - Enviando imagem para Docker Hub" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta

# Verificar se esta logado
Write-Host "[1/4] Verificando login no Docker Hub..." -ForegroundColor Cyan
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Voce nao esta logado no Docker!" -ForegroundColor Red
    Write-Host "Execute: docker login" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] Logado no Docker Hub" -ForegroundColor Green

# Tagear a imagem
Write-Host "[2/4] Tagando imagem..." -ForegroundColor Cyan
$fullImageName = "$DockerUsername/$imageName"
Write-Host "  Source: ${imageName}:${ImageTag}" -ForegroundColor Gray
Write-Host "  Target: ${fullImageName}:${ImageTag}" -ForegroundColor Gray

docker tag "${imageName}:${ImageTag}" "${fullImageName}:${ImageTag}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Erro ao tagear imagem!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Imagem tagada com sucesso" -ForegroundColor Green

# Fazer push
Write-Host "[3/4] Fazendo push da imagem (pode levar alguns minutos)..." -ForegroundColor Cyan
docker push "${fullImageName}:${ImageTag}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Erro ao fazer push!" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Push concluido com sucesso!" -ForegroundColor Green

# Verificar
Write-Host "[4/4] Verificando imagem no Docker Hub..." -ForegroundColor Cyan
Write-Host "  Link: https://hub.docker.com/r/${DockerUsername}/${imageName}" -ForegroundColor Cyan
Write-Host "  Comando para puxar: docker pull ${fullImageName}:${ImageTag}" -ForegroundColor Gray

Write-Host "============================================================" -ForegroundColor Green
Write-Host "SUCESSO! Imagem publicada no Docker Hub!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
