#!/usr/bin/env bash
#
# Restore the AMC PostgreSQL database from a gzipped pg_dump produced by
# backup.sh. THIS OVERWRITES THE TARGET DATABASE.
#
# Defaults target the docker-compose "db" service (see docker-compose.yml).
# Override with environment variables:
#   DB_SERVICE  compose service name   (default: db)
#   DB_NAME     database name          (default: amc)
#   DB_USER     database role          (default: amc)
#
# Usage:
#   scripts/restore.sh backups/amc-20260602-120000Z.sql.gz
#
set -euo pipefail

if [ "$#" -ne 1 ]; then
	echo "Usage: $0 <backup-file.sql.gz>" >&2
	exit 2
fi

backup_file="$1"
if [ ! -f "${backup_file}" ]; then
	echo "Backup file not found: ${backup_file}" >&2
	exit 1
fi

DB_SERVICE="${DB_SERVICE:-db}"
DB_NAME="${DB_NAME:-amc}"
DB_USER="${DB_USER:-amc}"

echo "Restoring '${DB_NAME}' from ${backup_file} (overwrites existing data)..." >&2
# --clean --if-exists in the dump drops existing objects first; ON_ERROR_STOP
# makes a partial/failed restore exit non-zero instead of silently continuing.
gunzip -c "${backup_file}" \
	| docker compose exec -T "${DB_SERVICE}" \
		psql --username "${DB_USER}" --dbname "${DB_NAME}" \
		--set ON_ERROR_STOP=on

echo "Restore complete." >&2
