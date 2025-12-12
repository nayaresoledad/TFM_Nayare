#!/bin/bash
set -euo pipefail

# This script is executed by the official Postgres image during initialization
# It creates the role `naynay` and grants privileges using the password from
# the environment variable POSTGRES_PASSWORD (do not commit secrets).

: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}"
: "${POSTGRES_DB:=tfm_db}"
: "${POSTGRES_USER:=postgres}"

# Use sed to escape single quotes in password
ESCAPED_PASSWORD=$(echo "$POSTGRES_PASSWORD" | sed "s/'/''/g")

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d "$POSTGRES_DB" <<EOSQL
DO
\$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'naynay') THEN
    CREATE ROLE naynay WITH LOGIN ENCRYPTED PASSWORD '$ESCAPED_PASSWORD';
  END IF;
END
\$\$;

GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO naynay;
EOSQL
