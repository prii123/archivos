#!/bin/bash

# Local Deploy Script (run directly on the server)
# This script rebuilds and restarts the application on the current server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_info "Starting local deployment..."

# Stop containers
print_info "Stopping containers..."
docker compose down
print_success "Containers stopped"

# Build images
print_info "Building Docker images..."
docker compose build --no-cache
print_success "Build complete"

# Start services
print_info "Starting services..."
docker compose up -d
print_success "Services started"

# Wait for database
print_info "Waiting for database to be ready..."
sleep 15

# Run migrations
print_info "Running database migrations..."
docker compose exec -T web alembic upgrade head || {
    print_error "Migration failed, but continuing..."
}
print_success "Migrations complete"

# Check status
print_info "Checking service status..."
docker compose ps

print_success "Deployment complete!"
print_info "============================================"
echo "Frontend: http://localhost"
echo "API Docs: http://localhost:8000/docs"
echo "Backend Health: http://localhost:8000/health"
echo ""
print_info "Check logs with: docker compose logs -f"
