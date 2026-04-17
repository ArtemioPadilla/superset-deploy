# Cloudflare Tunnel Configuration

This directory contains configuration for Cloudflare Tunnel integration.

## Quick Start

The easiest way to set up Cloudflare Tunnel is through the quick-start script:

```bash
./quick-start.sh
# When prompted "Enable Cloudflare Tunnel?", press 'y'
# Choose option 2 to enter your existing token
```

## Manual Configuration

### Option 1: Using Environment Variables (Recommended)

Set these in your `.env` file:
```bash
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-here
CLOUDFLARE_HOSTNAME=superset.yourdomain.com
```

### Option 2: Using Credentials File

If you have a `credentials.json` file from `cloudflared tunnel create`:
1. Copy it to this directory
2. Update `config.yaml` to reference it

## Getting a Tunnel Token

### New Tunnel
```bash
# Create a new tunnel
cloudflared tunnel create superset-tunnel

# Get the token
cloudflared tunnel token superset-tunnel
```

### Existing Tunnel
1. Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to Access > Tunnels
3. Click on your tunnel
4. Copy the token

## Configuration Files

- `config.yaml` - Defines ingress rules (which services to expose)
- `credentials.json` - (Optional) Tunnel credentials file
- `.env` - Environment variables including CLOUDFLARE_TUNNEL_TOKEN

## Troubleshooting

### Token Not Working
- Ensure the token is complete (very long string)
- Check if the tunnel exists in Cloudflare dashboard
- Verify the token hasn't been revoked

### Connection Issues
```bash
# Check tunnel logs
docker logs superset_cloudflared

# Test tunnel manually
cloudflared tunnel run --token YOUR-TOKEN
```