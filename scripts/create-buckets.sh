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
