# DigitalOcean Deployment

Single-host production deployment using Docker Compose, Caddy, Postgres, Redis,
and DigitalOcean Spaces.

## 1. Provision

1. Create an Ubuntu LTS Droplet.
2. Point DNS at the Droplet:
   - `A <domain>`
   - `A www.<domain>` if needed
3. Install Docker and the Compose plugin.
4. Clone or copy this repository onto the host.
5. Create a DigitalOcean Spaces bucket.

## 2. Environment

```bash
cp .env.example .env
```

Fill all required values from [../SETUP.md](../SETUP.md). For Spaces:

```text
S3_BUCKET=<bucket-name>
AWS_REGION=blr1
S3_ENDPOINT_URL=https://blr1.digitaloceanspaces.com
AWS_ACCESS_KEY_ID=<spaces-key>
AWS_SECRET_ACCESS_KEY=<spaces-secret>
```

Set the public domain in `Caddyfile` before starting Caddy.

## 3. Start

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Check status:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f gateway orchestrator-worker
curl https://<domain>/health
```

## 4. Meta Webhook

In Meta Developer Console, configure:

```text
Callback URL: https://<domain>/webhook/whatsapp
Verify token: value of WA_WEBHOOK_VERIFY_TOKEN
Subscribed field: messages
```

Use a permanent System User token for production.

## 5. Operational Checklist

- `DEBUG=false`
- Host firewall allows only SSH, 80, and 443.
- Postgres and Redis are not exposed publicly.
- Spaces bucket has encryption enabled.
- Sarvam spend cap is set.
- Caddy has obtained a valid certificate.
- Unit tests pass on the deployed commit.
- Backups are configured before storing real user ledger data.

## 6. Rollback

Keep the previous image/build available. To roll back:

```bash
git checkout <previous-known-good-commit>
docker compose -f docker-compose.prod.yml up -d --build
```

Database migrations in this repo are additive. Do not roll back data files
without a tested restore plan.
