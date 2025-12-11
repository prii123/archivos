# DocManager Drive - Local Development Script for Windows
# Este script configura y ejecuta el proyecto localmente en Docker
# Run con: powershell -ExecutionPolicy Bypass -File start-local.ps1

param(
    [Parameter(Mandatory=$false)]
    [switch]$Build,
    
    [Parameter(Mandatory=$false)]
    [switch]$Stop,
    
    [Parameter(Mandatory=$false)]
    [switch]$Restart,
    
    [Parameter(Mandatory=$false)]
    [switch]$Logs,
    
    [Parameter(Mandatory=$false)]
    [switch]$Clean,
    
    [Parameter(Mandatory=$false)]
    [switch]$Reset
)

$ErrorActionPreference = "Stop"

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Yellow
}

function Write-Title {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Check-Docker {
    Write-Info "Verificando Docker..."
    
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error-Custom "Docker no está instalado o no está en el PATH"
        Write-Host "Descarga Docker Desktop desde: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    $dockerRunning = docker info 2>$null
    if (-not $?) {
        Write-Error-Custom "Docker no está ejecutándose"
        Write-Host "Por favor inicia Docker Desktop y vuelve a intentar"
        exit 1
    }
    
    Write-Success "Docker está instalado y ejecutándose"
}

function Check-EnvFile {
    Write-Info "Verificando archivo .env..."
    
    if (-not (Test-Path ".env")) {
        Write-Info "Archivo .env no encontrado. Creando desde .env.example..."
        
        if (-not (Test-Path ".env.example")) {
            Write-Error-Custom "Archivo .env.example no encontrado"
            exit 1
        }
        
        Copy-Item ".env.example" ".env"
        Write-Success "Archivo .env creado"
        
        Write-Host ""
        Write-Host "⚠️  IMPORTANTE: Configura las siguientes variables en el archivo .env:" -ForegroundColor Yellow
        Write-Host "   1. ENCRYPTION_KEY - Genera con el comando que se muestra abajo" -ForegroundColor Yellow
        Write-Host "   2. JWT_SECRET - Cambia por una clave segura" -ForegroundColor Yellow
        Write-Host "   3. SUPERADMIN_EMAIL y SUPERADMIN_PASSWORD" -ForegroundColor Yellow
        Write-Host ""
        
        # Generar encryption key
        Write-Info "Generando ENCRYPTION_KEY..."
        try {
            $encryptionKey = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
            if ($encryptionKey) {
                Write-Host "Tu ENCRYPTION_KEY es: $encryptionKey" -ForegroundColor Green
                Write-Host "Cópiala en el archivo .env" -ForegroundColor Green
                
                # Intentar actualizar automáticamente
                $envContent = Get-Content ".env" -Raw
                $envContent = $envContent -replace "ENCRYPTION_KEY=your-fernet-key-here", "ENCRYPTION_KEY=$encryptionKey"
                Set-Content ".env" $envContent
                Write-Success "ENCRYPTION_KEY actualizada automáticamente en .env"
            }
        } catch {
            Write-Host "⚠️  No se pudo generar automáticamente. Genera manualmente con:" -ForegroundColor Yellow
            Write-Host "   python -c `"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())`"" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "Presiona Enter después de configurar .env para continuar..." -ForegroundColor Yellow
        Read-Host
    } else {
        Write-Success "Archivo .env encontrado"
    }
}

function Stop-Services {
    Write-Info "Deteniendo servicios..."
    docker compose down
    Write-Success "Servicios detenidos"
}

function Clean-Volumes {
    Write-Info "Limpiando volúmenes y contenedores..."
    
    docker compose down -v
    
    if (Test-Path "pgdata") {
        Write-Info "Eliminando directorio pgdata..."
        Remove-Item -Recurse -Force "pgdata" -ErrorAction SilentlyContinue
    }
    
    Write-Success "Limpieza completada"
}

function Build-Services {
    Write-Info "Construyendo imágenes Docker..."
    docker compose build
    Write-Success "Imágenes construidas"
}

function Start-Services {
    Write-Title "Iniciando DocManager Drive"
    
    Write-Info "Iniciando base de datos..."
    docker compose up -d db
    
    Write-Info "Esperando a que PostgreSQL esté listo..."
    Start-Sleep -Seconds 10
    
    # Verificar que la base de datos esté lista
    $retries = 0
    $maxRetries = 30
    while ($retries -lt $maxRetries) {
        $dbReady = docker compose exec -T db pg_isready -U postgres 2>$null
        if ($?) {
            Write-Success "Base de datos lista"
            break
        }
        $retries++
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
    
    if ($retries -eq $maxRetries) {
        Write-Error-Custom "Timeout esperando a la base de datos"
        exit 1
    }
    
    Write-Info "Iniciando servicios web..."
    docker compose up -d
    
    Write-Info "Esperando a que los servicios inicien..."
    Start-Sleep -Seconds 10
    
    Write-Success "Servicios iniciados"
}

function Run-Migrations {
    Write-Info "Ejecutando migraciones de base de datos..."
    
    docker compose exec -T web alembic upgrade head
    
    if ($?) {
        Write-Success "Migraciones completadas"
    } else {
        Write-Error-Custom "Error ejecutando migraciones"
        Write-Info "Puedes intentar manualmente con:"
        Write-Host "   docker compose exec web alembic upgrade head"
    }
}

function Create-Superadmin {
    Write-Info "Creando usuario superadmin..."
    
    docker compose exec -T web python app/scripts/create_superadmin.py
    
    if ($?) {
        Write-Success "Superadmin creado"
    } else {
        Write-Info "El superadmin puede que ya exista o hubo un error"
    }
}

function Show-Status {
    Write-Title "Estado de los Servicios"
    
    docker compose ps
    
    Write-Host ""
    Write-Info "URLs de acceso:"
    Write-Host "   Frontend:  http://localhost" -ForegroundColor Green
    Write-Host "   API:       http://localhost:8000" -ForegroundColor Green
    Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor Green
    Write-Host ""
}

function Show-Logs {
    Write-Info "Mostrando logs (Ctrl+C para salir)..."
    docker compose logs -f
}

function Test-Services {
    Write-Info "Probando servicios..."
    
    # Test health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "API está respondiendo correctamente"
        }
    } catch {
        Write-Error-Custom "API no está respondiendo"
        Write-Info "Verifica los logs con: docker compose logs web"
    }
    
    # Test frontend
    try {
        $response = Invoke-WebRequest -Uri "http://localhost" -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Success "Frontend está respondiendo correctamente"
        }
    } catch {
        Write-Error-Custom "Frontend no está respondiendo"
        Write-Info "Verifica los logs con: docker compose logs nginx"
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "DocManager Drive - Script de Desarrollo Local" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso:" -ForegroundColor Yellow
    Write-Host "  .\start-local.ps1                # Inicia todo (primera vez)"
    Write-Host "  .\start-local.ps1 -Build         # Reconstruye imágenes e inicia"
    Write-Host "  .\start-local.ps1 -Stop          # Detiene servicios"
    Write-Host "  .\start-local.ps1 -Restart       # Reinicia servicios"
    Write-Host "  .\start-local.ps1 -Logs          # Muestra logs en tiempo real"
    Write-Host "  .\start-local.ps1 -Clean         # Limpia volúmenes y contenedores"
    Write-Host "  .\start-local.ps1 -Reset         # Reset completo (limpia y reinicia)"
    Write-Host ""
    Write-Host "Comandos útiles:" -ForegroundColor Yellow
    Write-Host "  docker compose ps                # Ver estado de servicios"
    Write-Host "  docker compose logs -f web       # Ver logs del backend"
    Write-Host "  docker compose logs -f nginx     # Ver logs del frontend"
    Write-Host "  docker compose exec web bash     # Acceder al contenedor backend"
    Write-Host "  docker compose exec db psql -U postgres docmanager  # Acceder a PostgreSQL"
    Write-Host ""
}

# Main Script Logic
Clear-Host

Write-Title "DocManager Drive - Desarrollo Local"

# Check prerequisites
Check-Docker

# Handle different commands
if ($Stop) {
    Stop-Services
    Write-Success "Servicios detenidos exitosamente"
    exit 0
}

if ($Clean) {
    $confirmation = Read-Host "¿Estás seguro de que quieres limpiar todos los datos? (s/n)"
    if ($confirmation -eq 's' -or $confirmation -eq 'S') {
        Clean-Volumes
        Write-Success "Limpieza completada"
    }
    exit 0
}

if ($Logs) {
    Show-Logs
    exit 0
}

if ($Restart) {
    Stop-Services
    Start-Sleep -Seconds 2
    Start-Services
    Show-Status
    Test-Services
    exit 0
}

if ($Reset) {
    $confirmation = Read-Host "¿Estás seguro de que quieres hacer un reset completo? Esto eliminará todos los datos. (s/n)"
    if ($confirmation -ne 's' -and $confirmation -ne 'S') {
        Write-Info "Reset cancelado"
        exit 0
    }
    
    Write-Title "Reset Completo"
    Clean-Volumes
    Check-EnvFile
    
    if ($Build) {
        Build-Services
    }
    
    Start-Services
    Run-Migrations
    Create-Superadmin
    Show-Status
    Test-Services
    
    Write-Title "Reset Completado"
    Write-Success "Sistema completamente reiniciado"
    exit 0
}

# Default: First run or normal start
Check-EnvFile

# Check if services are already running
$running = docker compose ps --services --filter "status=running" 2>$null
if ($running) {
    Write-Info "Los servicios ya están ejecutándose"
    $action = Read-Host "¿Qué deseas hacer? (1=Ver estado, 2=Reiniciar, 3=Ver logs, 4=Salir)"
    
    switch ($action) {
        "1" { 
            Show-Status
            Test-Services
        }
        "2" { 
            Stop-Services
            Start-Sleep -Seconds 2
            Start-Services
            Show-Status
            Test-Services
        }
        "3" { Show-Logs }
        default { exit 0 }
    }
    exit 0
}

# First time setup
Write-Title "Configuración Inicial"

if ($Build) {
    Build-Services
}

Start-Services
Run-Migrations
Create-Superadmin

Write-Host ""
Write-Title "¡Instalación Completada!"

Show-Status
Test-Services

Write-Host ""
Write-Info "Próximos pasos:"
Write-Host "   1. Abre http://localhost en tu navegador" -ForegroundColor Green
Write-Host "   2. Inicia sesión con las credenciales del .env" -ForegroundColor Green
Write-Host "   3. Configura las credenciales de Google Drive en el panel de admin" -ForegroundColor Green
Write-Host ""
Write-Info "Para ver los logs: .\start-local.ps1 -Logs"
Write-Info "Para detener: .\start-local.ps1 -Stop"
Write-Host ""

Write-Success "¡DocManager Drive está listo para usar!"
