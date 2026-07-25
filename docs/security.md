# Security and Reliability

This file documents controls that are implemented in the current codebase and
the remaining production risks.

## Ingress Controls

- Webhook POST requests are verified with Meta's `X-Hub-Signature-256` HMAC
  using `WA_APP_SECRET`.
- The webhook verify token is used only for Meta's GET subscription challenge.
- Meta retries are deduplicated in Redis for 24 hours using the WhatsApp
  message ID.
- Per-number rate limiting defaults to `MAX_MESSAGES_PER_HOUR=30`.
- Text input is truncated by `MAX_TEXT_MESSAGE_CHARS`.
- Audio and image downloads enforce size limits before expensive processing.

## Failure Isolation

- The gateway acknowledges valid webhook traffic quickly and dispatches slow
  work to Celery.
- STT exhaustion returns an empty transcript instead of throwing through the
  gateway.
- Model exhaustion raises `ModelUnavailableError`; orchestrator nodes convert
  it to friendly Bengali retry messages.
- Catalog poster generation falls back from Flux to Pillow to plain image plus
  caption.
- Plain-image catalog delivery handles presigned URL failure with a text
  fallback rather than crashing the turn.

## Financial Integrity

- Ledger entries are staged as `pending_ledger_entry` and require user
  confirmation before persistence.
- Ledger confirmation validates amount bounds and rejects NaN/Infinity.
- Pricing recommendations use deterministic floor/margin math.
- Negotiation decisions and counter-offers are deterministic and floor-safe.
- LLM-generated text is not trusted to produce financial numbers.

## Data Protection

- Postgres and Redis are private Docker services in the compose topology.
- Redis requires a password.
- S3 writes use server-side encryption flags.
- PDF rendering uses Jinja autoescape, tag stripping, and `base_url=None`.
- Market trend aggregation enforces a minimum distinct-seller threshold before
  producing advice.

## Cost Abuse Controls

- Redis rate limiting caps per-user message volume.
- Translation is gated by a local code-mix heuristic before calling Sarvam.
- Sarvam is the only paid AI vendor; set a dashboard spend cap before
  production use.
- Flux is optional; leave `FLUX_API_KEY` unset unless poster-generation spend
  is acceptable.

## Production Hardening Still Required

- Store secrets in a real secret manager for long-running production.
- Add host firewall rules and provider-level network restrictions.
- Configure backup/restore for Postgres and object storage.
- Add uptime monitoring for gateway, worker, Redis, Postgres, Sarvam, and S3.
- Rotate Meta and Sarvam credentials on a schedule.
- Revisit mTLS or private networking before multi-host deployment.
- Re-review Government Scheme RAG before enabling it for real users.
