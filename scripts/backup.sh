#!/usr/bin/env bash
#
# Back up the AMC PostgreSQL database to a timestamped, gzipped pg_dump.
#
# Defaults target the docker-compose "db" service (see docker-compose.yml).
# Override with environment variables:
#   DB_SERVICE  compose service name        (default: db)
#   DB_NAME     database name               (default: amc)
#   DB_USER     database role               (default: amc)
#   BACKUP_DIR  output directory            (default: backups)
#
# The dump uses --clean --if-exists so the companion restore.sh can replay it
# into a populated database without manual drops. Usage:
#
#   scripts/backup.sh
#
set -euo pipefail

DB_SERVICE="${DB_SERVICE:-db}"
DB_NAME="${DB_NAME:-amc}"
DB_USER="${DB_USER:-amc}"
BACKUP_DIR="${BACKUP_DIR:-backups}"

mkdir -p "${BACKUP_DIR}"
timestamp="$(date -u +%Y%m%d-%H%M%SZ)"
outfile="${BACKUP_DIR}/amc-${timestamp}.sql.gz"

echo "Backing up database '${DB_NAME}' from service '${DB_SERVICE}'..." >&2
docker compose exec -T "${DB_SERVICE}" \
	pg_dump --clean --if-exists --no-owner --username "${DB_USER}" "${DB_NAME}" \
	| gzip >"${outfile}"

echo "Wrote ${outfile}" >&2
# Emit the path on stdout so callers can capture it (e.g. for a restore drill).
echo "${outfile}"
