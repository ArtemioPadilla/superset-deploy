# 🚀 GCP Deployment Guide

Complete guide for deploying Apache Superset to Google Cloud Platform.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [GCP Project Setup](#gcp-project-setup)
- [Service Account Configuration](#service-account-configuration)
- [Deployment Options](#deployment-options)
  - [Free Tier Deployment](#free-tier-deployment)
  - [Standard Deployment](#standard-deployment)
  - [Production Deployment](#production-deployment)
- [Post-Deployment](#post-deployment)
- [Cost Monitoring](#cost-monitoring)
- [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

### Required Tools

```bash
# Check if tools are installed
gcloud version         # Google Cloud SDK
pulumi version        # Pulumi CLI
docker version        # Docker
python --version      # Python 3.8-3.11

# Install missing tools
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# Pulumi (installed by make setup)
make setup
```

### GCP Account Setup

1. **Create GCP Account**
   - Go to [cloud.google.com](https://cloud.google.com)
   - Sign up for free tier ($300 credit)

2. **Create Project**
   ```bash
   # Login to GCP
   gcloud auth login
   
   # Create new project
   gcloud projects create YOUR-PROJECT-ID \
     --name="Superset Deploy" \
     --set-as-default
   
   # Set project
   gcloud config set project YOUR-PROJECT-ID
   ```

3. **Enable Billing**
   ```bash
   # List billing accounts
   gcloud billing accounts list
   
   # Link billing account
   gcloud billing projects link YOUR-PROJECT-ID \
     --billing-account=BILLING-ACCOUNT-ID
   ```

## 🏗️ GCP Project Setup

### Enable Required APIs

```bash
# Enable all required APIs at once
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  compute.googleapis.com \
  container.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com \
  artifactregistry.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled
```

### Create Storage Buckets

```bash
# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1

# Create buckets for different purposes
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$PROJECT_ID-superset-data/
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$PROJECT_ID-superset-backups/
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://$PROJECT_ID-terraform-state/

# Set lifecycle rules for backups (optional)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [{
      "action": {"type": "Delete"},
      "condition": {"age": 30}
    }]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://$PROJECT_ID-superset-backups/
```

## 👤 Service Account Configuration

### Create Service Accounts

```bash
# Create service account for Superset
gcloud iam service-accounts create superset-sa \
  --display-name="Superset Service Account" \
  --description="Service account for Superset deployment"

# Create service account for Pulumi
gcloud iam service-accounts create pulumi-sa \
  --display-name="Pulumi Service Account" \
  --description="Service account for infrastructure deployment"
```

### Assign Permissions

```bash
# Set variables
export SA_EMAIL_SUPERSET=superset-sa@$PROJECT_ID.iam.gserviceaccount.com
export SA_EMAIL_PULUMI=pulumi-sa@$PROJECT_ID.iam.gserviceaccount.com

# Permissions for Superset
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL_SUPERSET" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL_SUPERSET" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL_SUPERSET" \
  --role="roles/secretmanager.secretAccessor"

# Permissions for Pulumi (deployment)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL_PULUMI" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL_PULUMI" \
  --role="roles/secretmanager.admin"
```

### Create Service Account Keys

```bash
# Create keys directory
mkdir -p keys

# Download keys
gcloud iam service-accounts keys create keys/superset-sa-key.json \
  --iam-account=$SA_EMAIL_SUPERSET

gcloud iam service-accounts keys create keys/pulumi-sa-key.json \
  --iam-account=$SA_EMAIL_PULUMI

# Set permissions
chmod 600 keys/*.json
```

## 🆓 Free Tier Deployment

Deploy Superset using only GCP free tier resources.

### 1. Configure system.yaml

```yaml
# Edit system.yaml
stacks:
  gcp-free-tier:
    type: minimal
    environment: gcp
    enabled: true  # Change this to true
    gcp:
      project_id: "YOUR-PROJECT-ID"  # Replace with your project
      region: "us-central1"          # Must be free tier region
      zone: "us-central1-a"
```

### 2. Set Environment Variables

```bash
# Create .env file
cat > .env << EOF
GCP_PROJECT=$PROJECT_ID
GCP_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=keys/pulumi-sa-key.json
SUPERSET_SECRET_KEY=$(openssl rand -base64 32)
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=$(openssl rand -base64 12)
EOF
```

### 3. Deploy

```bash
# Initialize Pulumi
cd pulumi
pulumi login --local
pulumi stack init gcp-free-tier

# Configure stack
pulumi config set gcp:project $PROJECT_ID
pulumi config set gcp:region us-central1

# Deploy
cd ..
make deploy ENV=gcp-free-tier

# This will output the Cloud Run URL
```

### 4. Verify Deployment

```bash
# Get service URL
gcloud run services describe superset \
  --region=us-central1 \
  --format="value(status.url)"

# Check service status
gcloud run services list --region=us-central1

# View logs
gcloud run services logs read superset --region=us-central1
```

## 🏢 Standard Deployment

For small to medium businesses with Cloud SQL and Redis.

### 1. Additional Setup

```bash
# Reserve static IP (optional)
gcloud compute addresses create superset-ip \
  --region=$REGION \
  --network-tier=STANDARD

# Create VPC network
gcloud compute networks create superset-network \
  --subnet-mode=custom \
  --bgp-routing-mode=regional

# Create subnet
gcloud compute networks subnets create superset-subnet \
  --network=superset-network \
  --region=$REGION \
  --range=10.0.0.0/24
```

### 2. Configure for Standard

```yaml
# system.yaml
stacks:
  staging:
    type: standard
    environment: gcp
    enabled: true
    gcp:
      project_id: "YOUR-PROJECT-ID"
      region: "us-central1"
    database:
      type: cloud-sql
      tier: "db-f1-micro"  # Or db-n1-standard-1
      disk_size: 10
      backup:
        enabled: true
        time: "02:00"
    cache:
      type: redis
      tier: "basic"
      memory_size_gb: 1
```

### 3. Deploy Standard

```bash
# Deploy
make deploy ENV=staging

# Get Cloud SQL connection info
gcloud sql instances describe superset-staging-db \
  --format="value(connectionName)"
```

## 🚀 Production Deployment

Enterprise-grade deployment on GKE with high availability.

### 1. Create GKE Cluster

```bash
# Create cluster
gcloud container clusters create superset-production \
  --region=$REGION \
  --num-nodes=3 \
  --machine-type=n1-standard-2 \
  --enable-autoscaling \
  --min-nodes=3 \
  --max-nodes=10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-cloud-logging \
  --enable-cloud-monitoring \
  --network=superset-network \
  --subnetwork=superset-subnet

# Get credentials
gcloud container clusters get-credentials superset-production \
  --region=$REGION
```

### 2. Configure for Production

```yaml
# system.yaml
stacks:
  production:
    type: production
    environment: gcp
    enabled: true
    gcp:
      project_id: "YOUR-PROJECT-ID"
      region: "us-central1"
    superset:
      replicas: 3
      resources:
        cpu: "2"
        memory: "4Gi"
    database:
      type: cloud-sql
      tier: "db-n1-standard-2"
      disk_size: 100
      high_availability: true
      backup:
        enabled: true
        time: "02:00"
        retention_days: 30
    cache:
      type: redis
      tier: "standard"
      memory_size_gb: 5
      high_availability: true
    monitoring:
      enabled: true
    security:
      vpc:
        enabled: true
      ssl:
        enabled: true
        managed: true
```

### 3. Deploy Production

```bash
# Deploy
make deploy ENV=production

# Get ingress IP
kubectl get ingress -n superset
```

## 📋 Post-Deployment

### 1. Configure DNS

```bash
# Get IP address
IP=$(gcloud compute addresses describe superset-ip \
  --region=$REGION \
  --format="value(address)")

# Add DNS record (example for Cloud DNS)
gcloud dns record-sets create superset.yourdomain.com \
  --zone=your-zone \
  --type=A \
  --ttl=300 \
  --rrdatas=$IP
```

### 2. Set Up SSL

```bash
# For Cloud Run (automatic)
# SSL is automatically provisioned

# For GKE with cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml

# Create certificate
cat << EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: superset-tls
  namespace: superset
spec:
  secretName: superset-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - superset.yourdomain.com
EOF
```

### 3. Configure Backup

```bash
# Create backup schedule for Cloud SQL
gcloud sql backups create \
  --instance=superset-production-db \
  --async

# Set up automated backups
gcloud sql instances patch superset-production-db \
  --backup-start-time=02:00 \
  --backup-configuration \
  --retained-backups-count=30 \
  --retained-transaction-log-days=7
```

### 4. Set Up Monitoring Alerts

```bash
# Create uptime check
gcloud monitoring uptime-check-configs create superset-uptime \
  --display-name="Superset Uptime Check" \
  --monitored-resource="{'type':'uptime_url','labels':{'host':'superset.yourdomain.com'}}" \
  --http-check="{'path':'/health','port':443,'use-ssl':true}" \
  --period=60

# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=YOUR-CHANNEL-ID \
  --display-name="Superset Down Alert" \
  --condition-display-name="Uptime check failed" \
  --condition="{\
    'displayName':'Uptime check failed',\
    'conditionThreshold':{\
      'filter':'metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\"',\
      'comparison':'COMPARISON_LT',\
      'thresholdValue':1,\
      'duration':'300s'\
    }\
  }"
```

## 💰 Cost Monitoring

### 1. Set Up Budget Alerts

```bash
# Create budget
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT_ID \
  --display-name="Superset Monthly Budget" \
  --budget-amount=50USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100 \
  --filter-projects=projects/$PROJECT_ID
```

### 2. Enable Cost Breakdown

```bash
# Label resources for cost tracking
gcloud run services update superset \
  --region=$REGION \
  --update-labels=app=superset,env=production,cost-center=analytics

# Export billing to BigQuery
gcloud billing accounts get-iam-policy $BILLING_ACCOUNT_ID > billing-iam.yaml
# Add BigQuery Data Editor role for export
```

### 3. Cost Optimization Script

```bash
# Create cost check script
cat > check-costs.sh << 'EOF'
#!/bin/bash
# Check current month costs

PROJECT_ID=$(gcloud config get-value project)
BILLING_ACCOUNT=$(gcloud billing projects describe $PROJECT_ID --format="value(billingAccountName)")

echo "=== Current Month Costs ==="
gcloud billing accounts describe $BILLING_ACCOUNT

echo -e "\n=== Resource Usage ==="
# Cloud Run
echo "Cloud Run:"
gcloud run services list --format="table(service,region,traffic)"

# Cloud SQL
echo -e "\nCloud SQL:"
gcloud sql instances list --format="table(name,tier,region)"

# Storage
echo -e "\nStorage:"
gsutil du -sh gs://${PROJECT_ID}-*

echo -e "\n=== Recommendations ==="
# Check for unused resources
UNUSED_DISKS=$(gcloud compute disks list --filter="users:[]" --format="value(name)")
if [ ! -z "$UNUSED_DISKS" ]; then
  echo "Found unused disks: $UNUSED_DISKS"
fi
EOF

chmod +x check-costs.sh
```

## 🔧 Troubleshooting

### Common Deployment Issues

#### API Not Enabled
```bash
# Error: API [run.googleapis.com] not enabled
# Solution:
gcloud services enable run.googleapis.com
```

#### Insufficient Permissions
```bash
# Error: Permission denied
# Solution: Check IAM roles
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

#### Cloud Run Service Not Found
```bash
# Check if service exists
gcloud run services list --region=all

# Check deployment logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

#### Database Connection Failed
```bash
# Test Cloud SQL connectivity
gcloud sql connect superset-db --user=postgres

# Check Cloud SQL proxy
kubectl logs -l app=cloud-sql-proxy -n superset

# Verify connection string
echo $DATABASE_URL
```

### Debug Commands

```bash
# View all resources
gcloud asset search-all-resources \
  --scope=projects/$PROJECT_ID \
  --query="labels.app=superset"

# Check quotas
gcloud compute project-info describe --project=$PROJECT_ID

# View recent errors
gcloud logging read "severity>=ERROR" --limit=20 --format=json

# Export logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=superset" \
  --format=json > superset-logs.json
```

### Performance Issues

```bash
# Check Cloud Run metrics
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"'

# Scale manually if needed
gcloud run services update superset \
  --min-instances=1 \
  --max-instances=10 \
  --region=$REGION

# Check database performance
gcloud sql operations list --instance=superset-db
```

## 🎯 Best Practices

1. **Security**
   - Always use service accounts, never user credentials
   - Enable VPC Service Controls for production
   - Use Secret Manager for all secrets
   - Enable audit logging

2. **Cost Management**
   - Set up budget alerts before deployment
   - Use committed use discounts for production
   - Enable auto-scaling with proper limits
   - Clean up unused resources regularly

3. **Reliability**
   - Always enable backups
   - Test restore procedures
   - Use health checks
   - Implement proper monitoring

4. **Performance**
   - Use regional resources when possible
   - Enable CDN for static assets
   - Implement caching strategies
   - Monitor and optimize queries

---

**Next Steps:**
- Set up [Monitoring](MONITORING.md)
- Configure [Security](SECURITY.md)
- Review [Production Checklist](PRODUCTION.md)
- Check [Cost Optimization](COST_OPTIMIZATION.md)