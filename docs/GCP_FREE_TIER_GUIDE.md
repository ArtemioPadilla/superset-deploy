# Guía Completa de GCP Free Tier para Superset

## ⚡ Quick Start - Desplegar en 10 minutos

### Requisitos Previos
```bash
# Instalar gcloud CLI
curl https://sdk.cloud.google.com | bash

# Login
gcloud auth login
gcloud config set project TU-PROYECTO-ID
```

### Despliegue Rápido
```bash
# 1. Clonar y configurar
git clone https://github.com/artemiopadilla/superset-deploy
cd superset-deploy
make setup

# 2. Habilitar APIs de GCP
gcloud services enable run.googleapis.com storage.googleapis.com

# 3. Configurar
cp system.yaml.example system.yaml
# Editar: gcp-free-tier.enabled = true
# Editar: gcp.project_id = "TU-PROYECTO-ID"

# 4. Desplegar
export GCP_PROJECT=TU-PROYECTO-ID
make deploy ENV=gcp-free-tier

# 5. Obtener URL
gcloud run services describe superset --region=us-central1 --format="value(status.url)"
```

**¡Listo!** Superset está corriendo en GCP por $0/mes 🎉

## 📋 Resumen de Límites del Free Tier

### Servicios Principales
- **Cloud Run**: 2M requests/mes, 360K GB-segundos, 180K vCPU-segundos
- **Cloud Storage**: 5 GB almacenamiento (solo regiones US)
- **Firestore**: 1 GB almacenamiento, 50K lecturas/día, 20K escrituras/día
- **Compute Engine**: 1 instancia e2-micro (0.25 vCPU, 1 GB RAM)
- **BigQuery**: 1 TB consultas/mes, 10 GB almacenamiento

### Servicios Adicionales
- **Cloud Build**: 2,500 minutos/mes
- **Pub/Sub**: 10 GB mensajes/mes
- **Secret Manager**: 6 versiones activas, 10K operaciones/mes
- **Artifact Registry**: 0.5 GB/mes
- **Cloud Functions**: 2M invocaciones/mes
- **Workflows**: 5K pasos internos, 2K llamadas HTTP/mes

## 🚀 Inicio Rápido

### 1. Configuración Local (Emulación Free Tier)

```bash
# Inicializar entorno
./scripts/init-free-tier.sh

# Copiar configuración
cp .env.free-tier .env

# Iniciar servicios
docker-compose -f docker/docker-compose.yaml -f docker/docker-compose.full-free-tier.yaml up -d

# Verificar estado
docker-compose ps
```

### 2. Acceso a Servicios

- **Superset**: http://localhost:8088 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 📊 Cálculos de Uso

### Escenario 1: Uso Personal (Dentro del Free Tier)
- **Patrón**: 2 horas/día, 5 días/semana
- **Cálculo**: 
  - 40 horas/mes = 144,000 segundos
  - RAM: 144,000 GB-segundos (40% del límite)
  - CPU: 72,000 vCPU-segundos (40% del límite)
- **Costo**: $0

### Escenario 2: Equipo Pequeño (Límite del Free Tier)
- **Patrón**: 8 horas/día, 5 días/semana
- **Cálculo**:
  - 160 horas/mes = 576,000 segundos
  - RAM: 576,000 GB-segundos (160% - excede límite)
  - CPU: 288,000 vCPU-segundos (160% - excede límite)
- **Costo estimado**: $20-30/mes

### Escenario 3: Uso Continuo (Excede Free Tier)
- **Patrón**: 24/7
- **Cálculo**:
  - 720 horas/mes = 2,592,000 segundos
  - Significativamente sobre límites
- **Costo estimado**: $50-100/mes

## 🔧 Optimizaciones para Free Tier

### 1. Scale to Zero (Crítico)
```yaml
autoscaling:
  enabled: true
  min_replicas: 0  # CRÍTICO para free tier
  max_replicas: 1
```

### 2. Límites de Recursos
```yaml
resources:
  cpu: "0.5"      # Usar menos CPU
  memory: "1Gi"   # Mínimo de RAM
```

### 3. Cache Agresivo
```python
# En superset_config.py
CACHE_DEFAULT_TIMEOUT = 86400  # 24 horas
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
}
```

### 4. Deshabilitar Features Costosos
```python
FEATURE_FLAGS = {
    'ALERTS_REPORTS': False,      # No Celery
    'SCHEDULED_QUERIES': False,   # No Celery
    'THUMBNAIL_CACHE_TTL': 0,     # No thumbnails
}
```

## 🚀 Migración a GCP

### 1. Preparación
```bash
# Instalar gcloud CLI
curl https://sdk.cloud.google.com | bash

# Autenticar
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Habilitar APIs Necesarias
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

### 3. Configurar system.yaml
```yaml
# Cambiar en system.yaml
gcp-full-free-tier:
  enabled: true  # Cambiar a true
  gcp:
    project_id: "your-actual-project"
```

### 4. Desplegar
```bash
# Usar Pulumi
make deploy ENV=gcp-full-free-tier

# O manualmente con gcloud
gcloud run deploy superset \
  --image=apache/superset:5.0.0 \
  --region=us-central1 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=1 \
  --allow-unauthenticated
```

## 📈 Monitoreo de Costos

### 1. Configurar Alertas de Presupuesto
```bash
# Crear presupuesto de $1
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="Free Tier Alert" \
  --budget-amount=1USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### 2. Verificar Uso Local
```bash
# Verificar límites
./scripts/check-limits.sh

# Ver estadísticas de Docker
docker stats

# Ver logs
docker-compose logs -f superset
```

### 3. Monitoreo en GCP
```bash
# Ver métricas de Cloud Run
gcloud run services describe superset \
  --region=us-central1 \
  --format="value(status.traffic[0].percent)"

# Ver uso de almacenamiento
gsutil du -s gs://your-bucket/
```

## 🛡️ Mejores Prácticas

### 1. Seguridad
- Cambiar contraseñas por defecto
- Habilitar HTTPS siempre
- Usar Secret Manager para credenciales
- Implementar reCAPTCHA

### 2. Performance
- Implementar cache en todos los niveles
- Usar consultas optimizadas
- Limitar tamaño de datasets
- Comprimir assets estáticos

### 3. Costos
- Revisar facturación diariamente
- Usar scale-to-zero siempre
- Limpiar datos antiguos regularmente
- Monitorear requests/segundo

## 🔧 Solución de Problemas

### Problema: Excediendo límites de requests
```bash
# Implementar rate limiting
docker-compose exec traefik \
  traefik --middlewares.rate-limit.ratelimit.average=20
```

### Problema: Base de datos lenta
```python
# Optimizar SQLite
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
```

### Problema: Memoria insuficiente
```yaml
# Reducir workers
GUNICORN_WORKERS: 1
SUPERSET_WEBSERVER_THREADS: 2
```

## 📚 Recursos Adicionales

- [GCP Free Tier](https://cloud.google.com/free/docs/free-cloud-features)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Superset Optimization](https://superset.apache.org/docs/installation/running-on-kubernetes)
- [Docker Resource Limits](https://docs.docker.com/config/containers/resource_constraints/)

## 🤝 Contribuir

Si encuentras formas de optimizar aún más para el free tier, por favor:
1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/optimization`
3. Commit cambios: `git commit -am 'Add optimization'`
4. Push: `git push origin feature/optimization`
5. Crea un Pull Request