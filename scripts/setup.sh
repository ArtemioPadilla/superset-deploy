#!/bin/bash
set -e

echo "🚀 Setting up Apache Superset deployment environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

# Convert to comparable numbers
current_version=$((python_major * 100 + python_minor))
min_version=308  # 3.8
max_version=311  # 3.11

# Check minimum version
if [ $current_version -lt $min_version ]; then
    echo "❌ Error: Python 3.8 or higher is required (found $python_version)"
    exit 1
fi

# Check maximum version and warn if higher
if [ $current_version -gt $max_version ]; then
    echo "⚠️  Warning: Python $python_version detected. Python 3.11 is recommended for best compatibility."
    echo "   You may experience compatibility issues with Python > 3.11"
    read -p "   Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Python $python_version detected"

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

# Create or activate virtual environment
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment in .venv..."
    python3 -m venv .venv
else
    echo "✅ Using existing virtual environment in .venv"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing development dependencies..."
pip install -r requirements-dev.txt

echo ""
echo "💡 Note: Only development dependencies were installed for faster setup."
echo "   To install all dependencies (including Pulumi), run: make install-full"

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
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Edit system.yaml to configure your stacks"
echo "3. Edit .env to set environment variables"
echo "4. Run 'make dev' to start local development"
echo "5. Run 'make deploy ENV=<environment>' to deploy to cloud"
echo ""
echo "💡 Tip: The Makefile automatically uses the virtual environment for Python commands"