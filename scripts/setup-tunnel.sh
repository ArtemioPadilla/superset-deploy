#!/bin/bash
set -e

echo "🔐 Setting up Cloudflare Tunnel for Apache Superset"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "📦 Installing cloudflared..."
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install cloudflared
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        # Add Cloudflare GPG key
        sudo mkdir -p --mode=0755 /usr/share/keyrings
        curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
        
        # Add repo
        echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
        
        # Install
        sudo apt-get update && sudo apt-get install cloudflared
    else
        echo "❌ Unsupported OS. Please install cloudflared manually."
        echo "Visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation"
        exit 1
    fi
fi

# Check if user is logged in to Cloudflare
if ! cloudflared tunnel list &> /dev/null; then
    echo "🔑 Please log in to Cloudflare..."
    cloudflared tunnel login
fi

# Function to create tunnel
create_tunnel() {
    local tunnel_name="$1"
    
    echo "🚇 Creating tunnel: $tunnel_name"
    
    # Check if tunnel already exists
    if cloudflared tunnel list | grep -q "$tunnel_name"; then
        echo "⚠️  Tunnel '$tunnel_name' already exists"
        read -p "Do you want to delete and recreate it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cloudflared tunnel delete "$tunnel_name"
        else
            return
        fi
    fi
    
    # Create tunnel
    cloudflared tunnel create "$tunnel_name"
    
    # Get tunnel ID
    tunnel_id=$(cloudflared tunnel list | grep "$tunnel_name" | awk '{print $1}')
    echo "✅ Tunnel created with ID: $tunnel_id"
    
    # Get credentials file path
    creds_file="$HOME/.cloudflared/${tunnel_id}.json"
    if [ -f "$creds_file" ]; then
        echo "📋 Credentials file: $creds_file"
        
        # Copy credentials to Docker directory
        if [ -d "docker/cloudflared" ]; then
            cp "$creds_file" docker/cloudflared/credentials.json
            echo "✅ Credentials copied to docker/cloudflared/"
        fi
    fi
    
    # Show tunnel token
    echo ""
    echo "🔑 To get your tunnel token for deployment, run:"
    echo "cloudflared tunnel token $tunnel_name"
    echo ""
    
    # Update .env file if it exists
    if [ -f ".env" ]; then
        echo "📝 Updating .env file..."
        
        # Update CLOUDFLARE_TUNNEL_ID
        if grep -q "CLOUDFLARE_TUNNEL_ID=" .env; then
            sed -i.bak "s/CLOUDFLARE_TUNNEL_ID=.*/CLOUDFLARE_TUNNEL_ID=$tunnel_id/" .env
        else
            echo "CLOUDFLARE_TUNNEL_ID=$tunnel_id" >> .env
        fi
        
        # Get tunnel token
        tunnel_token=$(cloudflared tunnel token "$tunnel_name")
        if [ -n "$tunnel_token" ]; then
            if grep -q "CLOUDFLARE_TUNNEL_TOKEN=" .env; then
                sed -i.bak "s/CLOUDFLARE_TUNNEL_TOKEN=.*/CLOUDFLARE_TUNNEL_TOKEN=$tunnel_token/" .env
            else
                echo "CLOUDFLARE_TUNNEL_TOKEN=$tunnel_token" >> .env
            fi
        fi
        
        echo "✅ .env file updated"
    fi
}

# Function to setup DNS
setup_dns() {
    local tunnel_name="$1"
    local hostname="$2"
    
    echo "🌐 Setting up DNS for $hostname..."
    
    # Route traffic to tunnel
    cloudflared tunnel route dns "$tunnel_name" "$hostname"
    
    echo "✅ DNS configured: $hostname → $tunnel_name"
}

# Main setup flow
echo ""
echo "Choose setup option:"
echo "1) Local development tunnel"
echo "2) Staging tunnel"
echo "3) Production tunnel"
echo "4) Custom tunnel"
read -p "Enter option (1-4): " option

case $option in
    1)
        tunnel_name="superset-dev"
        hostnames=("superset.local" "monitoring.local" "metrics.local")
        ;;
    2)
        tunnel_name="superset-staging"
        read -p "Enter your domain (e.g., staging.example.com): " domain
        hostnames=("superset.$domain" "monitoring.$domain" "metrics.$domain")
        ;;
    3)
        tunnel_name="superset-production"
        read -p "Enter your domain (e.g., example.com): " domain
        hostnames=("superset.$domain" "monitoring.$domain" "metrics.$domain")
        ;;
    4)
        read -p "Enter tunnel name: " tunnel_name
        read -p "Enter primary hostname: " primary_host
        hostnames=("$primary_host")
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

# Create tunnel
create_tunnel "$tunnel_name"

# Setup DNS for each hostname
if [ ${#hostnames[@]} -gt 0 ]; then
    echo ""
    echo "🌐 Setting up DNS routes..."
    for hostname in "${hostnames[@]}"; do
        # Only setup DNS for non-.local domains
        if [[ ! "$hostname" =~ \.local$ ]]; then
            setup_dns "$tunnel_name" "$hostname"
        else
            echo "⚠️  Skipping DNS setup for $hostname (.local domain)"
        fi
    done
fi

echo ""
echo "✅ Cloudflare Tunnel setup complete!"
echo ""
echo "Next steps:"
echo "1. Update system.yaml with your tunnel configuration"
echo "2. For local development: docker-compose --profile cloudflare up"
echo "3. For cloud deployment: make deploy ENV=<environment>"
echo ""
echo "To test your tunnel locally:"
echo "cloudflared tunnel run $tunnel_name"