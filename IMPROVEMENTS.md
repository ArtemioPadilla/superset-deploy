# Recent Improvements

## Cloudflare Tunnel Integration

### Enhanced Quick Start Experience
- **Interactive Token Input**: Users can now input their Cloudflare Tunnel token directly during quick-start
- **Token Detection**: If a token exists in environment variables, users are asked if they want to use it or enter a new one
- **Three Configuration Options**:
  1. Create new tunnel (runs setup script)
  2. Enter existing token (paste directly)
  3. Skip for now

### Token Management
- Tokens are automatically saved to `.env` files
- Token preview shows first 20 characters for confirmation
- Domain/hostname input is requested after token configuration
- Works with both minimal and full-stack deployments

### Documentation Updates
- Created comprehensive `CLOUDFLARE_TUNNEL_GUIDE.md`
- Added `FREE_TIER_CLARIFICATION.md` explaining that Cloudflare Tunnel is free
- Updated FAQ with Cloudflare Tunnel information
- Added README in `docker/cloudflared/` directory

### Docker Compose Updates
- Cloudflare service uses token from environment variable
- Simplified command: `tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}`
- Added to both main and generated full-stack compose files

## Free Tier Clarifications

### Clear Documentation
- Explicitly states that PostgreSQL and Redis are NOT included in GCP free tier
- SQLite is the only database option for true $0/month deployment
- Created comparison tables showing what's included vs what costs money
- Updated example configurations to remove misleading Cloud SQL references

### Quick Start Updates
- Free Tier option clearly shows it uses SQLite (not PostgreSQL)
- Added note that it "emulates GCP's actual free tier"
- Recommends Cloudflare Tunnel for free tier deployments

## Configuration Improvements

### Enhanced Validation
- URL validation for proper format
- CIDR notation validation for IP ranges
- Security checks for sensitive fields
- Better error messages with context

### Migration Tool
- Created `scripts/migrate_config.py` for upgrading configurations
- Handles environment variable expansion
- Preserves comments and formatting
- Backs up original files

### Better Examples
- Updated all examples to use Superset 5.0.0
- Added platform specifications for Apple Silicon compatibility
- Included resource limits for free tier emulation