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

docker exec -i "${PG_CONTAINER}" psql -U postgres -d postgres -v ro_password="${RO_PWD}" -v db_name="${DB_NAME}" <<'SQL'
-- Create role if missing, then ensure password
DO $do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'wodrag_ro') THEN
      CREATE ROLE wodrag_ro LOGIN PASSWORD :'ro_password';
   END IF;
END
$do$;

ALTER ROLE wodrag_ro LOGIN PASSWORD :'ro_password';

-- Allow connecting to the database
GRANT CONNECT ON DATABASE :"db_name" TO wodrag_ro;

\connect :"db_name"

-- Minimal privileges to read data
GRANT USAGE ON SCHEMA public TO wodrag_ro;
-- Grant on paradedb schema if it exists (ignore errors if not present)
DO $do$
BEGIN
   IF EXISTS (
     SELECT 1 FROM information_schema.schemata WHERE schema_name = 'paradedb'
   ) THEN
     EXECUTE 'GRANT USAGE ON SCHEMA paradedb TO wodrag_ro';
   END IF;
END
$do$;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO wodrag_ro;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT ON TABLES TO wodrag_ro;

-- Belt and suspenders: make sessions read-only by default
ALTER ROLE wodrag_ro SET default_transaction_read_only = on;
SQL

echo "Done. Ensure POSTGRES_RO_PASSWORD is set in your prod .env, then restart backend:"
echo "  docker compose -f docker-compose.prod.yml up -d --build backend"

