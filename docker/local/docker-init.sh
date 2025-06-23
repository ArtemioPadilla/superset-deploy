#!/bin/bash
set -e

echo "Starting Superset initialization..."

# Wait for database to be ready
echo "Waiting for database..."
if [[ "${DATABASE_URL}" == postgresql* ]]; then
    until psql "${DATABASE_URL}" -c '\q' 2>/dev/null; do
        echo "PostgreSQL is unavailable - sleeping"
        sleep 1
    done
    echo "PostgreSQL is up!"
fi

# Create admin user
echo "Creating admin user..."
superset fab create-admin \
    --username "${SUPERSET_ADMIN_USERNAME}" \
    --firstname Admin \
    --lastname User \
    --email "${SUPERSET_ADMIN_EMAIL}" \
    --password "${SUPERSET_ADMIN_PASSWORD}" || true

# Initialize database
echo "Initializing database..."
superset db upgrade

# Create default roles and permissions
echo "Setting up roles..."
superset init

# Load examples if requested
if [[ "${SUPERSET_LOAD_EXAMPLES}" == "yes" ]]; then
    echo "Loading example data..."
    superset load-examples || true
fi

echo "Superset initialization complete!"