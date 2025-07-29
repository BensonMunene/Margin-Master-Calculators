#!/bin/bash
# Simple deployment script with allow all hosts

set -e

echo "Deploying Django App with open access..."

# Allow all hosts
export ALLOWED_HOSTS="*"
export CSRF_TRUSTED_ORIGINS="http://*"
export DEBUG=False

# Stop existing containers
docker-compose down

# Start with new configuration
docker-compose up -d --build

echo "Deployment complete!"
echo "Application accessible from any IP"
echo "To view logs: docker-compose logs -f"