# Runbook: Restoring Postgres from a Blob Storage backup

Use this when the production database needs to be restored from a daily
backup (data corruption, bad migration, accidental destructive query, VM
rebuild). Written in advance so nobody is improvising `pg_restore` flags
during an actual incident.

## 1. List available backups

```bash
az storage blob list \
  --account-name <AZURE_STORAGE_ACCOUNT> \
  --container-name aisathi-backups \
  --prefix "postgres/" \
  --auth-mode login \
  --query "[].{name:name, modified:properties.lastModified}" \
  -o table
```

## 2. Download the backup you want

```bash
az storage blob download \
  --account-name <AZURE_STORAGE_ACCOUNT> \
  --container-name aisathi-backups \
  --name "postgres/<TIMESTAMP>.sql.gz" \
  --file restore.sql.gz \
  --auth-mode login
```

## 3. Restore into the running container

**Stop application traffic first** (writes during restore will conflict
with the incoming dump):

```bash
docker compose -f docker-compose.prod.yml stop gateway
```

Drop and recreate the database, then load the dump:

```bash
docker exec -it ai-sathi-postgres-1 psql -U aisathi -d postgres \
  -c "DROP DATABASE IF EXISTS aisathi;" \
  -c "CREATE DATABASE aisathi;"

gunzip -c restore.sql.gz | docker exec -i ai-sathi-postgres-1 psql -U aisathi -d aisathi
```

## 4. Bring the app back up

```bash
docker compose -f docker-compose.prod.yml start gateway
curl -f https://<your-domain>/health
```

## 5. Sanity-check the restore

```bash
docker exec -it ai-sathi-postgres-1 psql -U aisathi -d aisathi \
  -c "SELECT count(*) FROM users;" \
  -c "SELECT count(*) FROM ledger_entries;" \
  -c "SELECT max(entry_date) FROM ledger_entries;"
```

Compare row counts and the most recent `entry_date` against expectations
(e.g. "we know we had ~X users as of yesterday") — a restore that silently
succeeds but loaded a much older snapshot than intended is the failure
mode this check catches.

## Notes

- Backups are daily, so any restore loses up to ~24h of the most recent
  writes. If the incident is corruption-only (not full data loss), check
  whether the bad state can be fixed with a targeted `UPDATE`/`DELETE`
  instead of a full restore, to avoid losing that day's legitimate data.
- This procedure has not yet been run against a real production incident
  as of the last update to this doc — run it once as a drill against a
  scratch environment before trusting it blind. See the optional
  automated restore-drill note below.

## Optional: automated monthly restore drill

To catch a corrupted or empty backup automatically instead of discovering
it during a real outage, add a second systemd timer that, once a month,
restores the latest backup into a disposable scratch Postgres container
and checks `SELECT count(*) FROM users` returns a sane non-zero number,
alerting (e.g. via a webhook to a monitoring channel) if it doesn't. Not
included here to keep the initial rollout minimal — worth adding once the
daily backup itself has been running reliably for a few weeks.
