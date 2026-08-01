set -euo pipefail

: "${AZURE_STORAGE_ACCOUNT:?AZURE_STORAGE_ACCOUNT must be set}"
CONTAINER_NAME="${POSTGRES_CONTAINER_NAME:-ai-sathi-postgres-1}"
BLOB_CONTAINER="aisathi-backups"
RETENTION_DAYS=30

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_FILE="/tmp/aisathi-${TIMESTAMP}.sql.gz"

cleanup() {
  rm -f "$BACKUP_FILE"
}
trap cleanup EXIT

echo "[backup] dumping postgres from container ${CONTAINER_NAME}..."
docker exec "$CONTAINER_NAME" pg_dump -U aisathi -d aisathi | gzip > "$BACKUP_FILE"

if [ ! -s "$BACKUP_FILE" ]; then
  echo "[backup] ERROR: dump file is empty, refusing to upload" >&2
  exit 1
fi

echo "[backup] uploading to blob storage..."
az storage blob upload \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --container-name "$BLOB_CONTAINER" \
  --name "postgres/${TIMESTAMP}.sql.gz" \
  --file "$BACKUP_FILE" \
  --auth-mode login \
  --only-show-errors

echo "[backup] pruning backups older than ${RETENTION_DAYS} days..."
CUTOFF=$(date -u -d "${RETENTION_DAYS} days ago" +%Y-%m-%dT%H:%M:%SZ)
az storage blob list \
  --account-name "$AZURE_STORAGE_ACCOUNT" \
  --container-name "$BLOB_CONTAINER" \
  --prefix "postgres/" \
  --query "[?properties.lastModified < '${CUTOFF}'].name" \
  --auth-mode login \
  -o tsv \
| while read -r blob; do
    [ -z "$blob" ] && continue
    echo "[backup] deleting old blob: ${blob}"
    az storage blob delete \
      --account-name "$AZURE_STORAGE_ACCOUNT" \
      --container-name "$BLOB_CONTAINER" \
      --name "$blob" \
      --auth-mode login \
      --only-show-errors
  done

echo "[backup] complete: postgres/${TIMESTAMP}.sql.gz"
