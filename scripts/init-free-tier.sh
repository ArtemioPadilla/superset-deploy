#!/bin/bash
# Script to initialize local GCP Free Tier environment

set -e

echo "=== Initializing local GCP Free Tier environment ==="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to create directories
create_directories() {
    echo -e "${YELLOW}Creating directories for free tier...${NC}"
    
    # Main directories
    mkdir -p data/free-tier/{superset,storage,firestore,prometheus,grafana}
    
    # Cloud Storage directories (5GB limit)
    mkdir -p data/free-tier/storage/{uploads,images,backups}
    
    # Create limits file
    cat > data/free-tier/LIMITS.txt << EOF
GCP FREE TIER LIMITS:
=====================
- Cloud Run: 2M requests/month, 360K GB-seconds, 180K vCPU-seconds
- Cloud Storage: 5 GB (us-east1/west1/central1)
- Firestore: 1 GB storage, 50K reads/day, 20K writes/day
- Compute Engine: 1 e2-micro instance (0.25 vCPU, 1 GB RAM)
- Egress: 1 GB from North America
- BigQuery: 1 TB queries/month, 10 GB storage
- Pub/Sub: 10 GB messages/month
- Secret Manager: 6 active versions, 10K operations/month
- Cloud Build: 2,500 minutes/month
- Artifact Registry: 0.5 GB/month
EOF
    
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Función para configurar MinIO (Cloud Storage local)
setup_minio() {
    echo -e "${YELLOW}Configurando MinIO (Cloud Storage emulator)...${NC}"
    
    # Crear bucket script
    cat > scripts/create-buckets.sh << 'EOF'
#!/bin/bash
# Esperar a que MinIO esté listo
sleep 5

# Configurar alias de MinIO
mc alias set local http://minio:9000 minioadmin minioadmin

# Crear buckets
mc mb local/superset-data || true
mc mb local/superset-backups || true

# Configurar políticas
mc policy set public local/superset-data/public

# Configurar límites (5GB total)
mc admin config set local storage_class standard=EC:0

echo "MinIO buckets created"
EOF
    
    chmod +x scripts/create-buckets.sh
    echo -e "${GREEN}✓ MinIO configurado${NC}"
}

# Función para generar configuración de ejemplo
generate_env_file() {
    echo -e "${YELLOW}Generando archivo .env para free tier...${NC}"
    
    if [ ! -f .env.free-tier ]; then
        cat > .env.free-tier << EOF
# GCP Free Tier Environment Variables
# ====================================

# Proyecto GCP (cambiar cuando migre a GCP real)
GCP_PROJECT=my-gcp-project

# Superset Configuration
SUPERSET_VERSION=5.0.0
SUPERSET_PORT=8088
SUPERSET_SECRET_KEY=$(openssl rand -base64 32)
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_ADMIN_EMAIL=admin@example.com

# Free Tier Limits
MAX_REQUESTS_PER_MONTH=2000000
MAX_GB_SECONDS_PER_MONTH=360000
MAX_VCPU_SECONDS_PER_MONTH=180000

# Emulator Hosts
FIRESTORE_EMULATOR_HOST=firestore:8080
PUBSUB_EMULATOR_HOST=pubsub:8085
MINIO_ENDPOINT=http://minio:9000

# Monitoring
PROMETHEUS_RETENTION_DAYS=7
GRAFANA_ADMIN_PASSWORD=admin

# Cloud Storage Emulation
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
STORAGE_LIMIT_GB=5

# BigQuery Emulation (optional)
BIGQUERY_ENABLED=false
BIGQUERY_EMULATOR_HOST=

# Secret Manager Emulation
SECRET_MANAGER_PROJECT=local-free-tier
MAX_SECRET_VERSIONS=6
EOF
        echo -e "${GREEN}✓ Archivo .env.free-tier creado${NC}"
    else
        echo -e "${YELLOW}! Archivo .env.free-tier ya existe${NC}"
    fi
}

# Función para mostrar uso estimado
show_usage_calculator() {
    echo -e "${YELLOW}Calculadora de uso mensual:${NC}"
    cat << EOF

ESCENARIOS DE USO Y COSTOS:
===========================

1. Uso Mínimo (dentro del free tier):
   - 2 horas/día, 5 días/semana
   - Total: 40 horas/mes = 144,000 segundos
   - Con 1 GB RAM: 144,000 GB-segundos (40% del límite)
   - Con 0.5 vCPU: 72,000 vCPU-segundos (40% del límite)
   - Costo: \$0

2. Uso Moderado (puede exceder free tier):
   - 8 horas/día, 5 días/semana  
   - Total: 160 horas/mes = 576,000 segundos
   - Con 1 GB RAM: 576,000 GB-segundos (160% del límite)
   - Con 1 vCPU: 576,000 vCPU-segundos (320% del límite)
   - Costo estimado: ~\$20-30/mes

3. Uso Continuo (excede free tier):
   - 24/7 operación
   - Total: 720 horas/mes = 2,592,000 segundos
   - Significativamente sobre los límites
   - Costo estimado: ~\$50-100/mes

RECOMENDACIONES:
- Use scale-to-zero (min_replicas: 0)
- Configure Cloud Scheduler para despertar solo cuando necesite
- Implemente cache agresivo
- Monitoree uso con alertas de presupuesto

EOF
}

# Función para crear scripts de utilidad
create_utility_scripts() {
    echo -e "${YELLOW}Creando scripts de utilidad...${NC}"
    
    # Script para verificar límites
    cat > scripts/check-limits.sh << 'EOF'
#!/bin/bash
# Verificar uso actual vs límites free tier

echo "=== Verificación de límites GCP Free Tier ==="

# Verificar espacio en disco
echo -e "\n📁 Uso de almacenamiento (límite 5GB):"
du -sh data/free-tier/storage 2>/dev/null || echo "No data yet"

# Verificar base de datos
echo -e "\n🗄️  Tamaño de base de datos (límite 1GB):"
du -sh data/free-tier/superset/superset-free.db 2>/dev/null || echo "No database yet"

# Verificar contenedores en ejecución
echo -e "\n🐳 Recursos de contenedores:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep superset || true

# Calcular uso estimado mensual
echo -e "\n📊 Uso estimado mensual:"
echo "Para calcular su uso real, ejecute:"
echo "docker stats --no-stream"
EOF
    
    chmod +x scripts/check-limits.sh
    
    # Script para reset de datos
    cat > scripts/reset-free-tier.sh << 'EOF'
#!/bin/bash
# Reset del entorno free tier (útil para pruebas)

read -p "⚠️  Esto borrará todos los datos. ¿Continuar? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deteniendo servicios..."
    docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.full-free-tier.yaml down
    
    echo "Eliminando datos..."
    rm -rf data/free-tier/*
    
    echo "Reiniciando..."
    ./scripts/init-free-tier.sh
fi
EOF
    
    chmod +x scripts/reset-free-tier.sh
    
    echo -e "${GREEN}✓ Scripts de utilidad creados${NC}"
}

# Función principal
main() {
    echo -e "${GREEN}Inicializando entorno GCP Free Tier local...${NC}"
    
    # Verificar Docker
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker no está en ejecución${NC}"
        exit 1
    fi
    
    # Ejecutar pasos
    create_directories
    setup_minio
    generate_env_file
    create_utility_scripts
    show_usage_calculator
    
    echo -e "\n${GREEN}✅ Entorno GCP Free Tier inicializado${NC}"
    echo -e "\nPara iniciar el entorno:"
    echo -e "${YELLOW}1. Copie .env.free-tier a .env:${NC}"
    echo "   cp .env.free-tier .env"
    echo -e "${YELLOW}2. Inicie los servicios:${NC}"
    echo "   docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.full-free-tier.yaml up -d"
    echo -e "${YELLOW}3. Acceda a Superset:${NC}"
    echo "   http://localhost:8088 (admin/admin)"
    echo -e "${YELLOW}4. Monitoree uso:${NC}"
    echo "   ./scripts/check-limits.sh"
    echo -e "\n${YELLOW}Servicios adicionales:${NC}"
    echo "   - MinIO (Cloud Storage): http://localhost:9001"
    echo "   - Prometheus: http://localhost:9090"
    echo "   - Grafana: http://localhost:3000"
}

# Ejecutar
main