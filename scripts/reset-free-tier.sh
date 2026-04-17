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
