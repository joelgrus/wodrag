#!/usr/bin/env bash
set -euo pipefail

# Creates or updates a read-only role (wodrag_ro) and grants minimal privileges.
# Usage:
#   POSTGRES_RO_PASSWORD=your_password bash scripts/setup_readonly_role.sh
# Optional env:
#   DB_NAME (default: wodrag), PG_CONTAINER (default: wodrag_paradedb)

RO_PWD=${POSTGRES_RO_PASSWORD:-}
if [[ -z "${RO_PWD}" ]]; then
  echo "POSTGRES_RO_PASSWORD is required" >&2
  exit 1
fi

DB_NAME=${DB_NAME:-wodrag}
PG_CONTAINER=${PG_CONTAINER:-wodrag_paradedb}


echo "Creating/updating read-only role 'wodrag_ro' on database '${DB_NAME}' in container '${PG_CONTAINER}'..."

# Create role if missing (ignore error if exists)
docker exec -i "${PG_CONTAINER}" psql -U postgres -d postgres -c 'CREATE ROLE wodrag_ro LOGIN PASSWORD $$'"${RO_PWD}"'$$;' || true

# Ensure/refresh password
docker exec -i "${PG_CONTAINER}" psql -U postgres -d postgres -c 'ALTER ROLE wodrag_ro LOGIN PASSWORD $$'"${RO_PWD}"'$$;'

# Allow connecting to the target DB
docker exec -i "${PG_CONTAINER}" psql -U postgres -d postgres -c "GRANT CONNECT ON DATABASE ${DB_NAME} TO wodrag_ro;"

# Minimal privileges inside the DB
docker exec -i "${PG_CONTAINER}" psql -U postgres -d "${DB_NAME}" -c "GRANT USAGE ON SCHEMA public TO wodrag_ro;"

# Grant on paradedb schema if it exists
docker exec -i "${PG_CONTAINER}" psql -U postgres -d "${DB_NAME}" -c "DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'paradedb') THEN EXECUTE 'GRANT USAGE ON SCHEMA paradedb TO wodrag_ro'; END IF; END $$;"

# Table read access + default privileges
docker exec -i "${PG_CONTAINER}" psql -U postgres -d "${DB_NAME}" -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO wodrag_ro;"
docker exec -i "${PG_CONTAINER}" psql -U postgres -d "${DB_NAME}" -c "ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON TABLES TO wodrag_ro;"

# Make sessions read-only by default
docker exec -i "${PG_CONTAINER}" psql -U postgres -d postgres -c "ALTER ROLE wodrag_ro SET default_transaction_read_only = on;"

echo "Done. Ensure POSTGRES_RO_PASSWORD is set in your prod .env, then restart backend:"
echo "  docker compose -f docker-compose.prod.yml up -d --build backend"
