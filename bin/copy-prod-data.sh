#!/bin/bash
# Copy production database to local development environment
set -eu

# Get script location and project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Ensure backup directory exists
mkdir -p "$PROJECT_ROOT/iglo_dumps"

# Create backup of current development database first
echo "Creating backup of current local database..."
docker exec iglo-db pg_dump -Fc -U postgres > "$PROJECT_ROOT/iglo_dumps/iglo-dev-$(date +%Y%m%d).pg_dump"

# Fetch production database
echo "Fetching production database..."
ssh apps@iglo.szalenisamuraje.org 'docker exec iglo-production_db_1 pg_dump -Fc -U postgres' > "$PROJECT_ROOT/iglo_dumps/iglo_db.dump"

# Restore to local development
echo "Restoring production database to local development..."
cat "$PROJECT_ROOT/iglo_dumps/iglo_db.dump" | docker exec -i iglo-db pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-privileges --disable-triggers

echo "Database restore complete."