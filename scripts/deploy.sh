#!/bin/bash
set -e

# Default values
ENV="${1:-dev}"
ACTION="${2:-up}"

echo "🚀 Deploying Apache Superset - Environment: $ENV"

# Validate configuration
echo "🔍 Validating configuration..."
python3 scripts/validate.py

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check environment type
if [ "$ENV" = "dev" ]; then
    echo "📦 Starting local development environment..."
    docker-compose -f docker/docker-compose.yaml up -d
    echo "✅ Local development environment started!"
    echo "🌐 Access Superset at: http://localhost:8088"
    echo "👤 Default credentials: admin/admin"
else
    # Cloud deployment with Pulumi
    echo "☁️  Deploying to cloud environment: $ENV"
    
    # Check GCP credentials for cloud deployments
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        echo "❌ Error: No active GCP credentials found"
        echo "💡 Run: gcloud auth login"
        exit 1
    fi
    
    # Deploy with Pulumi
    cd pulumi
    pulumi stack select superset-$ENV 2>/dev/null || pulumi stack init superset-$ENV
    pulumi config set environment $ENV
    
    if [ "$ACTION" = "preview" ]; then
        pulumi preview
    elif [ "$ACTION" = "destroy" ]; then
        pulumi destroy
    else
        pulumi up
    fi
    
    cd ..
fi

echo "✅ Deployment complete!"