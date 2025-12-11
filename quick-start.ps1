# Quick Start Script - Simplified
# Para iniciar rápidamente el proyecto
# Run: .\quick-start.ps1

Write-Host ""
Write-Host "🚀 DocManager Drive - Quick Start" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "→ Verificando Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "✗ Docker no está instalado" -ForegroundColor Red
    Write-Host "  Descarga desde: https://www.docker.com/products/docker-desktop"
    exit 1
}

$dockerRunning = docker info 2>$null
if (-not $?) {
    Write-Host "✗ Docker no está ejecutándose. Inicia Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker OK" -ForegroundColor Green

# Check .env
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "→ Creando archivo .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env creado" -ForegroundColor Green
    
    # Generate encryption key
    try {
        $key = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        if ($key) {
            $content = Get-Content ".env" -Raw
            $content = $content -replace "ENCRYPTION_KEY=your-fernet-key-here", "ENCRYPTION_KEY=$key"
            Set-Content ".env" $content
            Write-Host "✓ ENCRYPTION_KEY generada" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Genera ENCRYPTION_KEY manualmente" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "→ Iniciando servicios..." -ForegroundColor Yellow

# Start services
docker compose up -d db
Start-Sleep -Seconds 8

docker compose up -d
Start-Sleep -Seconds 10

Write-Host "→ Ejecutando migraciones..." -ForegroundColor Yellow
docker compose exec -T web alembic upgrade head

Write-Host "→ Creando superadmin..." -ForegroundColor Yellow
docker compose exec -T web python app/scripts/create_superadmin.py

Write-Host ""
Write-Host "✓ ¡Todo listo!" -ForegroundColor Green
Write-Host ""
Write-Host "Accede a:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost" -ForegroundColor Green
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Detener: docker compose down" -ForegroundColor Yellow
Write-Host "Ver logs: docker compose logs -f" -ForegroundColor Yellow
Write-Host ""
