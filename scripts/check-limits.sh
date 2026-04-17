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
