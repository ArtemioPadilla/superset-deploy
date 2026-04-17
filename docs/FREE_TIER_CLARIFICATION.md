# 🆓 GCP Free Tier Clarification

## Important: What's Actually Free vs What Costs Money

### ✅ TRUE Free Tier Components (Actually $0/month)

| Service | Free Tier Limits | What We Use It For |
|---------|------------------|---------------------|
| **Cloud Run** | 2M requests/month<br>360K GB-seconds<br>180K vCPU-seconds | Running Superset |
| **Cloud Storage** | 5GB storage<br>1GB egress/month | Static files, exports |
| **Firestore** | 1GB storage<br>50K reads/day<br>20K writes/day | Session storage (optional) |
| **Cloud Build** | 120 minutes/day | Building container images |
| **Cloudflare Tunnel** | Unlimited tunnels<br>No bandwidth charges | Secure access without Load Balancer |

### ❌ NOT Free (These Cost Money!)

| Service | Minimum Cost | Why People Get Confused |
|---------|--------------|------------------------|
| **Cloud SQL** (PostgreSQL/MySQL) | ~$7-10/month | Has "free trial" but not "free tier" |
| **Memorystore** (Redis) | ~$30/month | No free tier at all |
| **Load Balancer** | ~$18/month | Often assumed to be free |
| **VPC NAT Gateway** | ~$45/month | Hidden cost many miss |

## 🎯 Our Free Tier Configurations

### Option 3: Free Tier Emulation
When you choose option 3 in `./quick-start.sh`, you get:
- ✅ **SQLite** database (NOT PostgreSQL)
- ✅ **SimpleCache** in-memory caching (NOT Redis)
- ✅ MinIO (emulates Cloud Storage)
- ✅ Firestore emulator
- ✅ Resource limits matching e2-micro

### Why No PostgreSQL or Redis?
```yaml
# This is what you get with Free Tier:
database:
  type: sqlite  # Free - runs in-process
  
# NOT this:
database:
  type: postgresql  # Costs $7+/month
  
cache:
  type: none  # Free - uses SimpleCache
  
# NOT this:
cache:
  type: redis  # Costs $30+/month
```

## 📊 Comparison: All Three Options

| Feature | Option 1: Minimal | Option 2: Full Stack | Option 3: Free Tier |
|---------|------------------|---------------------|---------------------|
| **Database** | SQLite | PostgreSQL | SQLite |
| **Cache** | None | Redis | None |
| **For Learning** | Superset UI | Production setup | GCP deployment |
| **Resource Limits** | No | No | Yes (1GB RAM) |
| **Cloud Emulators** | No | No | Yes |
| **Monthly Cost** | $0 | $0 (local) | $0 |

## 🔐 Cloudflare Tunnel - The Free Access Solution

Cloudflare Tunnel is **completely FREE** and perfect for our free tier deployment:

### Why Use Cloudflare Tunnel?
- ✅ **$0/month** - No bandwidth charges, unlimited tunnels
- ✅ **Replaces Load Balancer** - Saves $18/month
- ✅ **Zero Trust Security** - Enterprise-grade access control
- ✅ **No Public IP** - Your services stay private
- ✅ **DDoS Protection** - Cloudflare's global network
- ✅ **Easy Setup** - One command: `./scripts/setup-tunnel.sh`

### Setting Up Cloudflare Tunnel

#### Option 1: During Quick Start (NEW! 🎉)
```bash
# The quick-start script now asks if you want Cloudflare Tunnel!
./quick-start.sh

# When prompted "Enable Cloudflare Tunnel? [y/N]:", press 'y'
# The script will automatically set everything up
```

#### Option 2: Manual Setup
```bash
# 1. Run the setup script
./scripts/setup-tunnel.sh

# 2. Choose option 1 for local development
# 3. For cloud deployment, use your actual domain

# 4. Start with tunnel enabled
docker-compose --profile cloudflare up
```

📖 [Full Cloudflare Tunnel Guide](CLOUDFLARE_TUNNEL_GUIDE.md)

## 🚀 Deploying True Free Tier to GCP

To deploy a truly free Superset to GCP:

```yaml
# system.yaml configuration
stacks:
  gcp-free:
    environment: gcp
    database:
      type: sqlite  # MUST use SQLite
    cache:
      type: none    # MUST not use Redis
    superset:
      min_instances: 0  # Scale to zero
      max_instances: 1  # Limit scaling
    cloudflare:
      enabled: true  # Use tunnel instead of Load Balancer
      tunnel_name: "superset-free"
```

## ⚠️ Common Mistakes That Add Costs

1. **Using Cloud SQL**: Even db-f1-micro costs money
2. **Using Memorystore**: No free tier exists
3. **Not setting min_instances: 0**: Keeps running 24/7
4. **Using non-US regions**: Only US regions are free
5. **Adding Load Balancer**: Use Cloudflare tunnel instead

## 💡 Tips for Staying Free

1. **Always use SQLite** for database
2. **Never enable Redis** caching
3. **Set scale-to-zero** on Cloud Run
4. **Monitor with budget alerts** at $1
5. **Use Cloudflare tunnel** for access (not Load Balancer)
6. **Stay in US regions** (us-central1, us-east1, us-west1)

## 🤔 When to Use Each Option

- **Option 1 (Minimal)**: Quick testing, learning Superset features
- **Option 2 (Full Stack)**: Learning production deployment, testing with real databases
- **Option 3 (Free Tier)**: Testing GCP deployment, validating free tier limits

## 📈 If You Need PostgreSQL/Redis

If your use case requires PostgreSQL and Redis, you'll need to:
1. Choose Option 2 for local development (free on your machine)
2. Accept ~$50/month for GCP deployment with Cloud SQL + Memorystore
3. Or consider other cloud providers with better free tiers for databases