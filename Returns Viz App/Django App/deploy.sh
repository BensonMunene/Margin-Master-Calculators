#!/bin/bash
# Deployment script for ETF Returns Viz Django App

set -e

echo "ETF Returns Viz Django App Deployment Script"
echo "==========================================="

# Check if running on EC2
if [ ! -f /sys/hypervisor/uuid ] || [ `head -c 3 /sys/hypervisor/uuid` != "ec2" ]; then
    echo "Warning: This script is designed to run on an EC2 instance"
fi

# Configuration
APP_DIR="/home/ec2-user/etf-returns-viz"
REPO_URL="${REPO_URL:-}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."
if ! command_exists docker; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

if ! command_exists git; then
    echo "Error: Git is not installed"
    exit 1
fi

# Clone or update repository
if [ -n "$REPO_URL" ]; then
    echo "Setting up application from repository..."
    if [ -d "$APP_DIR" ]; then
        echo "Updating existing repository..."
        cd "$APP_DIR"
        git pull
    else
        echo "Cloning repository..."
        git clone "$REPO_URL" "$APP_DIR"
        cd "$APP_DIR"
    fi
    
    # Navigate to Django app directory
    cd "Returns Viz App/Django App"
else
    echo "No repository URL provided. Assuming code is already in place."
    if [ ! -d "$APP_DIR" ]; then
        echo "Error: Application directory not found at $APP_DIR"
        echo "Please clone the repository manually or provide REPO_URL"
        exit 1
    fi
    cd "$APP_DIR"
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p auth
mkdir -p ssl
mkdir -p Data

# Check if .htpasswd exists
if [ ! -f auth/.htpasswd ]; then
    echo ""
    echo "WARNING: No .htpasswd file found!"
    echo "Please create one with: htpasswd -c auth/.htpasswd username"
    echo ""
fi

# Check if .env file exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "Creating .env file from .env.example..."
        cp .env.example .env
        echo ""
        echo "WARNING: Please edit .env file with production values!"
        echo ""
    else
        echo "WARNING: No .env file found and no .env.example to copy from!"
    fi
fi

# Copy data files if they exist
if [ -d "../../Data" ]; then
    echo "Copying data files..."
    cp -r ../../Data/* Data/ 2>/dev/null || true
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start containers
echo "Building Docker images..."
docker-compose build

echo "Starting containers..."
docker-compose up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Check container status
echo ""
echo "Container status:"
docker-compose ps

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "Deployment successful!"
    echo ""
    echo "Application should be accessible at:"
    echo "http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "your-server-ip")"
    echo ""
    echo "Next steps:"
    echo "1. Create .htpasswd file if not exists: htpasswd -c auth/.htpasswd username"
    echo "2. Update .env file with production values"
    echo "3. Set up SSL certificate (see DEPLOYMENT_README.md)"
    echo "4. Configure CloudWatch monitoring"
else
    echo ""
    echo "Error: Some containers failed to start"
    echo "Check logs with: docker-compose logs"
    exit 1
fi