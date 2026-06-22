# Script melhorado para gerenciar Comandas API
# Inclui build, scan, e execução da API

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("build", "scan", "run-docker", "run-local", "all")]
    [string]$Action = "all"
)

$projectRoot = "c:\Users\isaque.santos\Documents\Desenvolvimento Web\Comandas_api\comandas_api"
$srcDir = Join-Path $projectRoot "src"
$certDir = Join-Path $projectRoot "cert"

# Cores para output
$colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-Header {
    param([string]$message)
    Write-Host "`n" -NoNewline
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor $colors.Header
    Write-Host "║ $($message.PadRight(63)) ║" -ForegroundColor $colors.Header
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor $colors.Header
}

function Write-Status {
    param([string]$message, [ValidateSet("success", "warning", "error", "info")][string]$type = "info")
    $symbol = @{
        success = "✓"
        warning = "⚠"
        error = "✗"
        info = "►"
    }
    $color = $colors[$type]
    Write-Host "$($symbol[$type]) $message" -ForegroundColor $color
}

function Build-Docker {
    Write-Header "CONSTRUINDO IMAGEM DOCKER"
    
    Set-Location $projectRoot
    Write-Status "Construindo comandas_api:latest..." "info"
    
    docker build -t comandas_api:latest .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Imagem Docker construída com sucesso!" "success"
        return $true
    } else {
        Write-Status "Erro ao construir imagem Docker!" "error"
        return $false
    }
}

function Scan-Docker {
    Write-Header "ESCANEANDO VULNERABILIDADES"
    
    Write-Status "Escaneando vulnerabilidades com Docker Scout..." "info"
    docker scout cves comandas_api:latest
    
    Write-Status "Scan completo!" "success"
}

function Run-Local {
    Write-Header "EXECUTANDO API LOCALMENTE"
    
    Set-Location $srcDir
    Write-Status "Iniciando API com Uvicorn (HTTPS na porta 4443)..." "info"
    Write-Status "Swagger UI: https://localhost:4443/docs" "success"
    Write-Status "Pressione CTRL+C para parar..." "warning"
    
    Start-Sleep -Seconds 2
    
    ..\venv\Scripts\python.exe -m uvicorn main:app `
        --host 0.0.0.0 `
        --port 4443 `
        --ssl-certfile "$certDir\cert.pem" `
        --ssl-keyfile "$certDir\ecc-key.pem" `
        --reload
}

function Run-Docker {
    Write-Header "EXECUTANDO API EM DOCKER"
    
    Write-Status "Iniciando container Docker..." "info"
    Write-Status "Swagger UI: https://localhost:4443/docs" "success"
    Write-Status "Pressione CTRL+C para parar..." "warning"
    
    docker run --rm `
        --name comandas-api `
        -p 4443:4443 `
        -v "${certDir}:/cert" `
        -v "${srcDir}:/app" `
        --health-cmd='curl -f https://localhost:4443/health --insecure || exit 1' `
        --health-interval=30s `
        --health-timeout=10s `
        comandas_api:latest
}

function Show-Menu {
    Write-Header "COMANDAS API - PAINEL DE CONTROLE"
    Write-Host ""
    Write-Host "  1) [BUILD] Construir imagem Docker" -ForegroundColor $colors.Info
    Write-Host "  2) [SCAN]  Verificar vulnerabilidades" -ForegroundColor $colors.Info
    Write-Host "  3) [RUN]   Executar API localmente (Uvicorn)" -ForegroundColor $colors.Info
    Write-Host "  4) [RUN]   Executar API em Docker" -ForegroundColor $colors.Info
    Write-Host "  5) [ALL]   Build + Scan + Executar localmente" -ForegroundColor $colors.Info
    Write-Host "  0) [EXIT]  Sair" -ForegroundColor $colors.Warning
    Write-Host ""
    $choice = Read-Host "Escolha uma opção"
    return $choice
}

# Executar ação
switch ($Action) {
    "build" {
        Build-Docker
    }
    "scan" {
        Scan-Docker
    }
    "run-local" {
        Run-Local
    }
    "run-docker" {
        Run-Docker
    }
    "all" {
        if (Build-Docker) {
            Scan-Docker
            Write-Header "INICIANDO API"
            $runChoice = Read-Host "Deseja executar a API? (1=Local, 2=Docker, 0=Não)"
            switch ($runChoice) {
                "1" { Run-Local }
                "2" { Run-Docker }
                default { Write-Status "Operação concluída!" "success" }
            }
        }
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor $colors.Header
Write-Status "Pressione ENTER para continuar..." "info"
Read-Host
