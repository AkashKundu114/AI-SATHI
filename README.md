# Kotha-Khata

Voice-first WhatsApp assistant for West Bengal SHG sellers. It handles Bengali
bookkeeping, price guidance, negotiation support, catalog poster creation, and
market trend advice through the official Meta WhatsApp Cloud API.

This repository is production-oriented: no prototype-only docs, no alternate
messaging providers, and no stale model-vendor instructions. The active
documentation set is intentionally small and listed in [docs/README.md](docs/README.md).

## Production Stack

| Layer | Implementation |
|---|---|
| WhatsApp ingress | `services/gateway`, FastAPI webhook, Meta HMAC verification |
| Async execution | Celery worker running the LangGraph orchestrator |
| Conversation state | LangGraph state with Postgres checkpointing |
| Data stores | Postgres with pgvector, Redis for idempotency/rate limits |
| AI vendor | Sarvam AI primary; local Ollama / faster-whisper fallback |
| Object storage | S3-compatible bucket, DigitalOcean Spaces-ready |
| Public TLS | Caddy in `docker-compose.prod.yml` |

## Active Features

- Voice ledger: Bengali audio/text to income and expense entries, with
  confirm/correct flow before database writes.
- Ledger reports: monthly PDF report with totals, continuity signals, SHG
  metadata, and Bengali calendar context.
- Pricing recommendation: deterministic floor and margin math; LLM only
  phrases the explanation.
- Negotiation support: deterministic accept/reject and counter-offers; LLM
  cannot invent price numbers.
- Catalog creator: product image processing, vision classification, Bengali
  captions, optional Flux poster generation, and local Pillow fallback.
- Market predictor: block-level, k-anonymized trend aggregation with optional
  mandi price context.
- General conversation: bounded, on-topic Bengali fallback replies.

Government scheme RAG exists in code but is not part of the active production
route. Treat it as disabled until it is explicitly wired and re-reviewed.

## Quick Start

```bash
make setup
# Fill .env from .env.example
make check-env
make dev
```

Run tests:

```bash
make test
```

For production deployment, use [SETUP.md](SETUP.md) first, then
[docs/digitalocean-deploy.md](docs/digitalocean-deploy.md).

## Required Configuration

Minimum required values:

- Meta WhatsApp Cloud API: `WA_PHONE_NUMBER_ID`, `WA_ACCESS_TOKEN`,
  `WA_WEBHOOK_VERIFY_TOKEN`, `WA_APP_SECRET`
- Postgres and Redis credentials: `POSTGRES_PASSWORD`, `REDIS_PASSWORD`,
  `DATABASE_URL`, `REDIS_URL`
- Sarvam AI key for production model calls: `SARVAM_API_KEY`
- S3-compatible storage for images and PDFs

Strongly recommended for production: set `USE_LOCAL_MODELS=true` and provision
Ollama plus faster-whisper fallback capacity. With Sarvam as the only paid AI
vendor, local fallback is the uptime plan.

## Repository Layout

```text
services/
  gateway/             WhatsApp webhook, signature checks, media intake
  orchestrator/        LangGraph state machine, model router, feature nodes
  voice_gateway/       Saaras V3 to faster-whisper STT cascade
  pdf_service/         Monthly report generation and S3 upload
  vision_service/      Product image analysis and poster composition
  market_service/      K-anonymized market aggregation
shared/
  config/              Runtime settings
  db/                  SQLAlchemy models and sessions
  i18n/                Bengali calendar and number helpers
  knowledge/           Dignity, seasonal, and negotiation context
  storage/             S3 client
  whatsapp/            Parser, media download, sender
migrations/            SQL migrations applied on fresh container boot
tests/unit/            Offline unit coverage for core behavior
docs/                  Current production and reviewer documentation
```

## Reviewer Entry Points

- [docs/architecture.md](docs/architecture.md)
- [docs/security.md](docs/security.md)
- [docs/engineering-review.md](docs/engineering-review.md)
- [docs/COST.md](docs/COST.md)

## License

AGPLv3. See [LICENSE](LICENSE).
