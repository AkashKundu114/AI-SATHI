# Architecture

Kotha-Khata is a stateful WhatsApp agent for SHG sellers. The architecture is
built around one production constraint: Meta must receive a fast webhook ACK,
while slow voice, vision, model, PDF, and storage work happens asynchronously.

## Request Flow

```text
Meta WhatsApp Cloud API
  -> services/gateway FastAPI webhook
  -> Redis idempotency + per-number rate limit
  -> media download / STT / raw image upload
  -> Celery task
  -> services/orchestrator LangGraph
  -> feature node
  -> WhatsApp outbound sender
```

The gateway verifies `X-Hub-Signature-256` with `WA_APP_SECRET`, deduplicates
Meta retries by message ID, rate-limits each phone number, and returns `200`
unless authentication fails. The heavy work runs in `orchestrator-worker`.

## Services

| Service | Responsibility |
|---|---|
| `services/gateway` | Webhook verification, request shaping, media intake, queue dispatch. |
| `services/orchestrator` | LangGraph state machine and feature nodes. |
| `services/voice_gateway` | STT cascade: Saaras V3 first, faster-whisper fallback. |
| `services/translation_service` | Sarvam chat, vision, and translation clients. |
| `services/pdf_service` | Monthly PDF reports and S3 upload. |
| `services/vision_service` | Image cleanup, product analysis, captions, poster composition. |
| `services/market_service` | k-anonymized block-level trend aggregation. |
| `shared/*` | Config, DB, storage, WhatsApp helpers, i18n, and shared knowledge. |

## State Machine

`services/orchestrator/graph.py` owns routing. Each user turn carries a typed
conversation state through one node at a time. Feature-specific nodes return
state updates, outbound messages, and trace labels.

Important nodes:

- `intent_router.py`: maps text/transcript to an active feature.
- `ledger_node.py`: extracts pending ledger transactions.
- `ledger_confirm_node.py`: confirms or corrects pending transactions before
  DB writes.
- `ledger_confirm_flow_node.py`: handles WhatsApp Flow confirmation payloads.
- `pricing_node.py`: computes deterministic price recommendations.
- `negotiation_node.py`: computes deterministic negotiation decisions.
- `price_chat_node.py`: seller-facing price discussion before catalog posting.
- `catalog_node.py`: image-to-catalog flow.
- `market_predictor_node.py`: market trend advice.
- `conversation_node.py`: bounded fallback conversation.

## Model Router

All text, translation, and vision model calls go through
`services/orchestrator/model_router.py`.

| Call type | Primary | Fallback |
|---|---|---|
| Text agents | Sarvam `sarvam-30b` or `sarvam-105b` | local Ollama `qwen2.5` |
| Vision | Sarvam Vision | local Ollama `qwen2-vl` |
| Translation | Sarvam translate | self-hosted translate endpoint, then Ollama |
| STT | Saaras V3 | faster-whisper |

There is no OpenAI, Claude, Twilio, or Baileys dependency in the active runtime.
If Sarvam is unavailable and local fallback is disabled, model calls raise
`ModelUnavailableError`; nodes convert that into Bengali retry messages.

## Deterministic Safety Invariants

The highest-risk user-visible values are computed in code, not by the model:

- Ledger writes happen only after confirmation.
- Ledger amounts reject non-finite or unreasonable values.
- Pricing floor and recommendation math live in `pricing_node.py`.
- Negotiation accept/reject and counter-offers are code-computed.
- Negotiation and pricing messages are checked so model text cannot introduce
  below-floor rupee values.
- Market predictor requires the aggregator's k-anonymity floor before trends are
  produced.
- PDF report fields are escaped and cleaned before rendering.

## Storage and Persistence

- Postgres stores users, SHGs, ledger entries, seller profiles, catalog items,
  market prices, and pgvector-backed data.
- Redis stores webhook deduplication keys and rate-limit counters.
- S3-compatible storage holds raw/processed catalog images and generated PDFs.
- Migrations are mounted into the Postgres container for fresh deployment boot.

## Production Topology

`docker-compose.prod.yml` runs:

- `postgres`
- `redis`
- `gateway`
- `orchestrator-worker`
- `caddy`

This is a single-host production topology suitable for pilot and small
deployment traffic. Before multi-host deployment, revisit internal network
trust, managed Postgres/Redis, backups, worker autoscaling, and secrets
management.

## Disabled or Non-Primary Areas

Government Scheme RAG is present in code but not part of active production
routing. It should not be advertised as deployed until routing, migrations,
data seeding, and grounding checks are re-reviewed together.
