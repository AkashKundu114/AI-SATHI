# Setup

Production setup for Kotha-Khata using the official Meta WhatsApp Cloud API.

## 1. Prerequisites

- Docker and Docker Compose plugin
- A Meta Developer app with the WhatsApp product enabled
- A Sarvam AI API key
- An S3-compatible bucket
- A public HTTPS domain for production webhooks

For local testing, `ngrok http 8000` is enough to receive Meta webhooks.

## 2. Configure WhatsApp Cloud API

In Meta Developers:

1. Create a Business app.
2. Add the WhatsApp product.
3. Copy the phone number ID into `WA_PHONE_NUMBER_ID`.
4. Create or copy an access token into `WA_ACCESS_TOKEN`.
5. Copy App Secret into `WA_APP_SECRET`.
6. Choose a random webhook verify token and set it in
   `WA_WEBHOOK_VERIFY_TOKEN`.

Webhook callback URL:

```text
https://<your-domain>/webhook/whatsapp
```

Subscribe the WhatsApp product to `messages` webhooks.

For production traffic, replace temporary test tokens with a permanent System
User token and complete Meta Business Verification.

## 3. Configure `.env`

```bash
make setup
```

Edit `.env` and fill:

```text
WA_PHONE_NUMBER_ID=
WA_ACCESS_TOKEN=
WA_WEBHOOK_VERIFY_TOKEN=
WA_APP_SECRET=

POSTGRES_PASSWORD=
REDIS_PASSWORD=
DATABASE_URL=postgresql+asyncpg://kothkori:<password>@postgres:5432/kothkori
REDIS_URL=redis://:<password>@redis:6379/0

SARVAM_API_KEY=

S3_BUCKET=
AWS_REGION=
S3_ENDPOINT_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

Then validate:

```bash
make check-env
```

## 4. Local Model Fallback

For production, enable local fallback:

```text
USE_LOCAL_MODELS=true
```

Start and pull models:

```bash
docker compose --profile local-models up -d ollama
docker compose exec ollama ollama pull qwen2.5:7b-instruct-q4_K_M
docker compose exec ollama ollama pull qwen2-vl:7b-q4_K_M
```

STT fallback uses `faster-whisper` through the voice gateway provider.

## 5. Optional Features

WhatsApp Flow confirmation:

```text
WA_LEDGER_CONFIRM_FLOW_ID=
```

This requires Meta Business Verification. If unset, ledger confirmation uses
plain text replies.

Catalog poster font:

```text
BENGALI_FONT_PATH=assets/fonts/NotoSansBengali-VariableFont_wdth,wght.ttf
```

If the font is missing, catalog delivery falls back to photo plus caption.

Flux poster upgrade:

```text
FLUX_API_KEY=
FLUX_BASE_URL=https://api.bfl.ml
```

If unset or failing, local Pillow poster generation remains available.

## 6. Run Locally

```bash
make dev
```

Health check:

```bash
curl http://localhost:8000/health
```

## 7. Production Readiness Checklist

- `DEBUG=false`
- Permanent Meta System User token configured
- `WA_APP_SECRET` and `WA_WEBHOOK_VERIFY_TOKEN` are different values
- Sarvam dashboard spend cap set
- Redis and Postgres passwords changed from defaults
- S3 bucket encryption enabled
- Public domain points to the deployment host
- TLS is terminated by Caddy or equivalent
- `USE_LOCAL_MODELS=true` tested if production uptime matters
- `pytest tests/unit/` passes before deploy
