# Script para configurar PostgreSQL localmente en Windows
# Ejecuta como administrador: powershell -ExecutionPolicy Bypass -File setup-postgres.ps1

Write-Host ""
Write-Host "🐘 Configuración de PostgreSQL para DocManager Drive" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Opción 1: Usar Chocolatey para instalar PostgreSQL
Write-Host "Opción 1: Instalar PostgreSQL con Chocolatey" -ForegroundColor Yellow
Write-Host ""
Write-Host "Ejecuta estos comandos en PowerShell como Administrador:" -ForegroundColor White
Write-Host ""
Write-Host "# Instalar Chocolatey si no lo tienes:" -ForegroundColor Cyan
Write-Host 'Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString(''https://community.chocolatey.org/install.ps1''))' -ForegroundColor Gray
Write-Host ""
Write-Host "# Instalar PostgreSQL:" -ForegroundColor Cyan
Write-Host "choco install postgresql -y" -ForegroundColor Gray
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opción 2: Descargar instalador manual" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Ve a: https://www.postgresql.org/download/windows/" -ForegroundColor White
Write-Host "2. Descarga el instalador" -ForegroundColor White
Write-Host "3. Instala con estas opciones:" -ForegroundColor White
Write-Host "   - Usuario: postgres" -ForegroundColor Gray
Write-Host "   - Contraseña: postgres" -ForegroundColor Gray
Write-Host "   - Puerto: 5432" -ForegroundColor Gray
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opción 3: Usar Docker Desktop (Recomendado)" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Descarga Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor White
Write-Host "2. Instala y reinicia Windows" -ForegroundColor White
Write-Host "3. Ejecuta: docker compose up -d db" -ForegroundColor White
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Después de instalar PostgreSQL:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Crea la base de datos:" -ForegroundColor Cyan
Write-Host '   psql -U postgres -c "CREATE DATABASE docmanager;"' -ForegroundColor Gray
Write-Host ""
Write-Host "2. Vuelve a ejecutar uvicorn:" -ForegroundColor Cyan
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""

Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
$choice = Read-Host "¿Qué opción prefieres? (1=Chocolatey, 2=Manual, 3=Docker, Enter=Salir)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "→ Verificando Chocolatey..." -ForegroundColor Yellow
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "→ Instalando Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    }
    
    Write-Host "→ Instalando PostgreSQL..." -ForegroundColor Yellow
    choco install postgresql -y
    
    Write-Host ""
    Write-Host "✓ PostgreSQL instalado!" -ForegroundColor Green
    Write-Host "→ Creando base de datos..." -ForegroundColor Yellow
    
    Start-Sleep -Seconds 5
    & "C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres -c "CREATE DATABASE docmanager;"
    
    Write-Host "✓ Listo! Ahora ejecuta: uvicorn app.main:app --reload" -ForegroundColor Green
}
elseif ($choice -eq "2") {
    Start-Process "https://www.postgresql.org/download/windows/"
    Write-Host "✓ Abriendo página de descarga..." -ForegroundColor Green
}
elseif ($choice -eq "3") {
    Start-Process "https://www.docker.com/products/docker-desktop"
    Write-Host "✓ Abriendo página de Docker Desktop..." -ForegroundColor Green
}
else {
    Write-Host "Saliendo..." -ForegroundColor Yellow
}
