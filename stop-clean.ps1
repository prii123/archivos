# Stop and Clean Script
# Para detener servicios y limpiar datos
# Run: .\stop-clean.ps1

param(
    [Parameter(Mandatory=$false)]
    [switch]$KeepData
)

Write-Host ""
Write-Host "🛑 DocManager Drive - Stop & Clean" -ForegroundColor Red
Write-Host "===================================" -ForegroundColor Red
Write-Host ""

if ($KeepData) {
    Write-Host "→ Deteniendo servicios (manteniendo datos)..." -ForegroundColor Yellow
    docker compose down
    Write-Host "✓ Servicios detenidos. Datos preservados." -ForegroundColor Green
} else {
    Write-Host "⚠️  Esto eliminará todos los datos (base de datos, archivos)." -ForegroundColor Yellow
    $confirm = Read-Host "¿Continuar? (s/n)"
    
    if ($confirm -eq 's' -or $confirm -eq 'S') {
        Write-Host "→ Deteniendo servicios y eliminando datos..." -ForegroundColor Yellow
        docker compose down -v
        
        if (Test-Path "pgdata") {
            Remove-Item -Recurse -Force "pgdata" -ErrorAction SilentlyContinue
            Write-Host "✓ Directorio pgdata eliminado" -ForegroundColor Green
        }
        
        Write-Host "✓ Servicios detenidos y datos eliminados" -ForegroundColor Green
    } else {
        Write-Host "✗ Operación cancelada" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Para iniciar nuevamente: .\quick-start.ps1" -ForegroundColor Cyan
Write-Host ""
