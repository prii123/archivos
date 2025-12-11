# Script para ejecutar la aplicación con Docker
# Ejecuta: .\run-app.ps1

Write-Host ""
Write-Host "🚀 Iniciando DocManager Drive con Docker" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Docker
Write-Host "→ Verificando Docker..." -ForegroundColor Yellow
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "✗ Docker no está instalado" -ForegroundColor Red
    exit 1
}

$dockerRunning = docker info 2>$null
if (-not $?) {
    Write-Host "✗ Docker no está ejecutándose. Por favor inicia Docker Desktop." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker OK" -ForegroundColor Green

# Ir al directorio del proyecto
Set-Location "c:\Users\wowpr\Desktop\proyectos\archivador\docmanager-drive"

# Verificar .env
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "→ Creando archivo .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    
    # Generar ENCRYPTION_KEY
    Write-Host "→ Generando ENCRYPTION_KEY..." -ForegroundColor Yellow
    try {
        $key = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        if ($key) {
            $content = Get-Content ".env" -Raw
            $content = $content -replace "ENCRYPTION_KEY=your-fernet-key-here", "ENCRYPTION_KEY=$key"
            Set-Content ".env" $content
            Write-Host "✓ .env configurado" -ForegroundColor Green
        }
    } catch {
        Write-Host "⚠️  Configura ENCRYPTION_KEY manualmente en .env" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "→ Iniciando servicios con Docker Compose..." -ForegroundColor Yellow
Write-Host ""

# Iniciar base de datos primero
docker compose up -d db
Write-Host "→ Esperando PostgreSQL..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Iniciar todos los servicios
docker compose up -d

Write-Host ""
Write-Host "→ Esperando que los servicios inicien..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Ejecutar migraciones
Write-Host "→ Ejecutando migraciones..." -ForegroundColor Yellow
docker compose exec -T web alembic upgrade head

# Crear superadmin
Write-Host "→ Creando superadmin..." -ForegroundColor Yellow
docker compose exec -T web python app/scripts/create_superadmin.py

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "✓ ¡Aplicación iniciada exitosamente!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Accede a la aplicación en:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost" -ForegroundColor Green
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  API:       http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Credenciales por defecto (ver .env):" -ForegroundColor Yellow
Write-Host "  Email:     admin@example.com" -ForegroundColor White
Write-Host "  Password:  changeme123" -ForegroundColor White
Write-Host ""
Write-Host "Comandos útiles:" -ForegroundColor Cyan
Write-Host "  Ver logs:     docker compose logs -f" -ForegroundColor White
Write-Host "  Detener:      docker compose down" -ForegroundColor White
Write-Host "  Reiniciar:    docker compose restart" -ForegroundColor White
Write-Host ""
