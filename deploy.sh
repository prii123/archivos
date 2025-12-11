#!/bin/bash

# DocManager Drive Deployment Script
# This script deploys the application to a DigitalOcean droplet or any Linux server

set -e

# Configuration
REMOTE_USER="${DEPLOY_USER:-root}"
REMOTE_HOST="${DEPLOY_HOST}"
REMOTE_DIR="${DEPLOY_DIR:-/opt/docmanager-drive}"
PROJECT_NAME="docmanager-drive"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check required environment variables
if [ -z "$REMOTE_HOST" ]; then
    print_error "DEPLOY_HOST environment variable is required"
    echo "Usage: DEPLOY_HOST=your-server.com ./deploy.sh"
    exit 1
fi

print_info "Starting deployment to $REMOTE_HOST..."

# Create deployment package
print_info "Creating deployment package..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="${PROJECT_NAME}_${TIMESTAMP}.tar.gz"

tar -czf "$PACKAGE_NAME" \
    --exclude='pgdata' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log' \
    .

print_success "Package created: $PACKAGE_NAME"

# Upload to server
print_info "Uploading to server..."
scp "$PACKAGE_NAME" "${REMOTE_USER}@${REMOTE_HOST}:/tmp/"
print_success "Upload complete"

# Deploy on server
print_info "Deploying on server..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" << ENDSSH
set -e

# Create directory if not exists
sudo mkdir -p $REMOTE_DIR
cd $REMOTE_DIR

# Backup existing deployment
if [ -d "current" ]; then
    echo "Creating backup..."
    sudo cp -r current backup_\$(date +%Y%m%d_%H%M%S) || true
fi

# Extract new deployment
echo "Extracting package..."
sudo rm -rf new_deployment
sudo mkdir -p new_deployment
sudo tar -xzf /tmp/$PACKAGE_NAME -C new_deployment
sudo rm /tmp/$PACKAGE_NAME

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

# Check if .env exists, if not copy from .env.example
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

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 15

# Run migrations
echo "Running Alembic migrations..."
sudo docker compose exec -T web alembic upgrade head

# Create superadmin
echo "Creating superadmin user..."
sudo docker compose exec -T web python app/scripts/create_superadmin.py || true

# Check health
echo "Checking application health..."
curl -f http://localhost:8000/health || echo "Warning: Health check failed"

echo "✅ Deployment complete!"
echo "Application is running at: http://$REMOTE_HOST"

ENDSSH

print_success "Deployment completed successfully!"

# Cleanup local package
rm "$PACKAGE_NAME"
print_info "Cleaned up local package"

print_info "============================================"
print_success "Deployment Summary"
print_info "============================================"
echo "Server: $REMOTE_HOST"
echo "Directory: $REMOTE_DIR/current"
echo "Frontend: http://$REMOTE_HOST"
echo "API Docs: http://$REMOTE_HOST/docs"
echo ""
print_info "Next steps:"
echo "1. SSH to server and configure .env file"
echo "2. Update SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD"
echo "3. Generate ENCRYPTION_KEY with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
echo "4. Restart services: cd $REMOTE_DIR/current && sudo docker compose restart"
echo "5. Configure SSL with Let's Encrypt (see README.md)"
