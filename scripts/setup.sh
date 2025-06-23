#!/bin/bash
set -e

echo "🚀 Setting up Apache Superset deployment environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [[ $(echo "$python_version >= $required_version" | bc) -ne 1 ]]; then
    echo "❌ Error: Python $required_version or higher is required (found $python_version)"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running. Please start Docker."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Node dependencies
if command -v npm &> /dev/null; then
    echo "📦 Installing Node dependencies..."
    npm install
else
    echo "⚠️  Warning: npm not found. Skipping Node dependencies."
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration values"
fi

# Create system.yaml if it doesn't exist
if [ ! -f system.yaml ]; then
    echo "📝 Creating system.yaml from example..."
    cp system.yaml.example system.yaml
    echo "⚠️  Please update system.yaml with your stack configurations"
fi

# Initialize Pulumi
echo "🔧 Initializing Pulumi..."
cd pulumi
pulumi login --local
cd ..

# Create data directory for local development
mkdir -p data

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit system.yaml to configure your stacks"
echo "2. Edit .env to set environment variables"
echo "3. Run 'make dev' to start local development"
echo "4. Run 'make deploy ENV=<environment>' to deploy to cloud"