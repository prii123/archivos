# DocManager Drive Deployment Script for Windows
# Run with: powershell -ExecutionPolicy Bypass -File deploy.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$RemoteHost,
    
    [Parameter(Mandatory=$false)]
    [string]$RemoteUser = "root",
    
    [Parameter(Mandatory=$false)]
    [string]$RemoteDir = "/opt/docmanager-drive"
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

Write-Info "Starting deployment to $RemoteHost..."

# Create deployment package
Write-Info "Creating deployment package..."
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$packageName = "docmanager-drive_$timestamp.tar.gz"

# Check if tar is available
if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
    Write-Error-Custom "tar command not found. Please install tar or use WSL."
    exit 1
}

# Create tar archive (excluding unnecessary files)
tar -czf $packageName `
    --exclude='pgdata' `
    --exclude='__pycache__' `
    --exclude='*.pyc' `
    --exclude='.git' `
    --exclude='node_modules' `
    --exclude='*.log' `
    .

Write-Success "Package created: $packageName"

# Upload to server
Write-Info "Uploading to server..."
scp $packageName "${RemoteUser}@${RemoteHost}:/tmp/"
Write-Success "Upload complete"

# Deploy on server
Write-Info "Deploying on server..."
$deployScript = @"
set -e

# Create directory if not exists
sudo mkdir -p $RemoteDir
cd $RemoteDir

# Backup existing deployment
if [ -d "current" ]; then
    echo "Creating backup..."
    sudo cp -r current backup_`$(date +%Y%m%d_%H%M%S) || true
fi

# Extract new deployment
echo "Extracting package..."
sudo rm -rf new_deployment
sudo mkdir -p new_deployment
sudo tar -xzf /tmp/$packageName -C new_deployment
sudo rm /tmp/$packageName

# Stop running containers
if [ -d "current" ]; then
    echo "Stopping existing containers..."
    cd current
    sudo docker compose down || true
    cd ..
fi

# Move new deployment to current
sudo rm -rf current
sudo mv new_deployment current
cd current

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    sudo cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration!"
fi

# Run database migrations
echo "Running database migrations..."
sudo docker compose up -d db
sleep 10

# Build and start services
echo "Building and starting services..."
sudo docker compose build
sudo docker compose up -d

# Wait for services
echo "Waiting for services to start..."
sleep 15

# Run migrations
echo "Running Alembic migrations..."
sudo docker compose exec -T web alembic upgrade head

# Create superadmin
echo "Creating superadmin user..."
sudo docker compose exec -T web python app/scripts/create_superadmin.py || true

# Health check
echo "Checking application health..."
curl -f http://localhost:8000/health || echo "Warning: Health check failed"

echo "✅ Deployment complete!"
echo "Application is running at: http://$RemoteHost"
"@

ssh "${RemoteUser}@${RemoteHost}" $deployScript

Write-Success "Deployment completed successfully!"

# Cleanup
Remove-Item $packageName
Write-Info "Cleaned up local package"

Write-Info "============================================"
Write-Success "Deployment Summary"
Write-Info "============================================"
Write-Host "Server: $RemoteHost"
Write-Host "Directory: $RemoteDir/current"
Write-Host "Frontend: http://$RemoteHost"
Write-Host "API Docs: http://$RemoteHost/docs"
Write-Host ""
Write-Info "Next steps:"
Write-Host "1. SSH to server and configure .env file"
Write-Host "2. Update SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD"
Write-Host "3. Generate ENCRYPTION_KEY"
Write-Host "4. Restart services: cd $RemoteDir/current && sudo docker compose restart"
Write-Host "5. Configure SSL with Let's Encrypt (see README.md)"
