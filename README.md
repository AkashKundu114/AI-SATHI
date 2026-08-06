# AI-SATHI (AI-সাথী)

Voice-first WhatsApp bot for West Bengal SHG women — bookkeeping, pricing
guidance, product catalog creation, and market intelligence, entirely in
spoken Bengali.

Messaging runs exclusively on the **official Meta WhatsApp Cloud API** — no
Twilio, no Baileys, no other third-party messaging provider.

**AI vendors, and why each one:**
- **Sarvam AI** — sole external AI vendor. `sarvam-30b` for standard-tier
  structured text (ledger extraction, corrections, market phrasing, pricing
  explanations), `sarvam-105b` for higher-stakes phrasing (ad captions,
  negotiation), `sarvam-vision` for catalog photo identification, and
  `saaras:v3` for speech-to-text. **There is no OpenAI dependency anywhere
  in this codebase** — see `docs/architecture.md` §8.
- **Flux Pro** (optional) — poster-generation upgrade. Leave `FLUX_API_KEY`
  blank and posters are still generated locally via Pillow, free, always.
- **Self-hosted fallback (local Ollama, strongly recommended)** — the *only*
  fallback tier for every text/vision agent now that OpenAI has been
  removed, and also serves local embeddings (`nomic-embed-text`) for the
  Scheme RAG seeding pipeline. `faster-whisper` remains the dedicated free
  STT fallback regardless of this setting. See `docs/COST.md` for the full
  cascade table.

## What's here

| Feature | What it does |
|---|---|
| **Voice-Ledger** | Bengali voice note → Banglish/code-mixed normalization (only when needed) → structured income/expense extraction → confirm/correct loop → database write → bank-submittable PDF (continuity months, SHG grading, bank-linkage status, declaration + sign-off line). Confirmation can be a tap-to-confirm **WhatsApp Flow** (optional, `WA_LEDGER_CONFIRM_FLOW_ID`) instead of typed হ্যাঁ/না, removing typo/mishearing risk on the way to a permanent write — see `docs/architecture.md` §10.3. |
| **Friend-style Pricing Chat** | A SELLER-facing conversational back-and-forth ("দর ঠিক করি একসাথে") to agree an asking price before a catalog poster is composed — warm, references seasonal/festival/district-mela timing from the shared knowledge base, never lets the model state a number, and hard-stops at the seller's own cost-derived floor rather than silently capping below it. See `docs/architecture.md` §10.4. |
| **Catalog Creator** | Product photo → background removal → vision product ID (Sarvam Vision, local Ollama vision fallback) → dual Bengali captions (Sarvam, dignity-guideline-constrained) → price suggestion (or the agreed price from the pricing chat above) → optional privacy-respecting market-demand note → composited into a single shareable ad poster (Flux Pro if configured, always falls back to a free local Pillow composite) |
| **Pricing Recommendation** | Deterministic price-floor/recommendation math from the seller's own cost, margin, and minimum price (`seller_profiles` table), blended with market data where available — Sarvam is used only to phrase the explanation, never to generate the number itself |
| **Negotiation** | Deterministic accept/reject against the same price floor, code-computed counter-offers (never LLM-generated), a post-generation safety scan that discards any LLM phrasing quoting below the floor, and a deterministically-chosen negotiation *tactic* (anchor / reciprocity / value-justification / graceful walk-away — `shared/knowledge/negotiation_playbook.py`) that the LLM only phrases, never picks — see `docs/architecture.md` §9.1 and §10.4 |
| **Cross-agent verification** | `services/orchestrator/nodes/cross_verify.py` — an independent second model call checks tone/dignity, combined with a deterministic check that every ₹ figure in a composed message matches a code-computed value, before the highest-stakes pricing-chat messages are sent. See `docs/architecture.md` §10.4. |
| **Market Predictor** | k-anonymized (min. 5 distinct sellers) aggregation of ledger sales data by block, fused with optional Agmarknet mandi price data, the shared festival/district-mela/seasonal knowledge base, and a West Bengal crop sowing/harvest calendar (`shared/knowledge/crop_calendar.py`) into rising/saturated trend advice and "this crop is at harvest, cheapest time to buy" notes |
| **Government Scheme RAG** | Hallucination-guarded (per-chunk, per-scheme grounding verification — catches "right amount, wrong scheme" citations), code-complete with a real seeding pipeline (`scripts/seed_schemes.py`), **not wired into current chat routing** — see `docs/archive/planning/scope.md` for the deliberate scope decision. Deliberately ships with **no pre-filled scheme content**; see `data/schemes/raw/README.md` for why. |
| **General conversation** | Off-topic messages get a real, warm, cheap (Sarvam-routed) reply that gently steers back on-topic |

Agri-diagnostics, meeting minutes, training, and subsidy matchmaking remain
valid product vision (`docs/product.md`) but are not in this build.

## Quick start

```bash
make setup     # copies .env.example -> .env, checks it, brings up Postgres
# now edit .env — fill in the REQUIRED section (see below)
make dev       # docker compose up --build
```

Postgres schema is applied automatically on first boot, in migration order:
`0001_init.sql` (core tables) → `0002_hybrid_search.sql` (scheme full-text
search — requires `0006` below to have run first if applying manually) →
`0004_seller_profile.sql` (Pricing agent) → `0005_shg_bank_linkage.sql`
(bank-loan PDF fields) → `0006_scheme_tables.sql` (creates `scheme_documents`/
`scheme_chunks`, fixing a documented gap where `0002` altered a table that
was never created — see that file's own header). No separate migration step
needed for a fresh `docker-entrypoint-initdb.d` boot; for a manual `psql -f`
apply against an existing database, apply `0006` before `0002` if `0002`
hasn't successfully run yet.

Run the test suite any time (no API keys or network required):
```bash
make test
```
389 tests, all deterministic/offline — covers ledger validation, grounding
verification, pricing/negotiation floors, graph routing, the shared
knowledge base (festivals, district melas, crop calendar, life-cycle
occasions), Bengali digit/number-word handling, and the scheme-seeding
script's chunking logic.

## What you must provide

Two things are required to run this at all:

1. **A WhatsApp Cloud API app** (Meta Developer account → WhatsApp product →
   Phone Number ID + Access Token + App Secret + a verify token you choose
   yourself). See `SETUP.md` for the exact click-through.
2. **A Sarvam AI key** (`sarvam.ai`) — this is now the sole paid AI vendor.

Strongly recommended: enable `USE_LOCAL_MODELS=true` with a self-hosted
Ollama box (pull `nomic-embed-text` too if you plan to seed Scheme RAG
content). With no OpenAI fallback anymore, this is the only thing that
keeps every agent alive during a Sarvam outage — see `docs/COST.md`.

Optional, and safe to leave unset: `WA_LEDGER_CONFIRM_FLOW_ID` (tap-to-confirm
ledger Flow - falls back to plain text if unset), S3 bucket, Langfuse,
`DATA_GOV_IN_API_KEY` (Agmarknet mandi prices), Flux Pro, Bengali font for
poster generation.

## Architecture, in one paragraph

`services/gateway` is the FastAPI webhook receiver — it verifies Meta's HMAC
signature, deduplicates retried webhooks, rate-limits per number, and hands
off to Celery so the 20-second WhatsApp ack window is never at risk.
`services/orchestrator` is a LangGraph state machine (Postgres-checkpointed,
so every conversation turn is resumable) with one node per agent.
`services/orchestrator/model_router.py` is the single place any LLM/vision/
translation call goes through — a two-tier Sarvam → local-Ollama cascade for
every agent, with retries and hard timeouts, raising a typed
`ModelUnavailableError` that every node catches and turns into a friendly
Bengali message instead of a crash. `shared/knowledge/` is the single
source of cultural/seasonal/market-timing context (statewide festivals,
district-specific fairs, life-cycle occasions across Hindu/Muslim/Christian
Bengali communities, a West Bengal crop sowing/harvest calendar, negotiation
tactics, and tone/dignity rules) every agent reads from instead of each node
inventing its own.

Full design rationale: see `docs/architecture.md` (§8 for the OpenAI
removal, §10 for the shared knowledge base / dignity rules / Flow-verified
ledger / friend pricing chat / negotiation tactics / cross-verification)
and `docs/security.md` / `docs/red-team.md` for what's hardened and why. Step-by-step first-run instructions: see
`SETUP.md`. For a detailed summary of the late-2026 update session (including
the complete stripping of comments, environment and ignore configurations,
weasyprint adjustments, and Sarvam PDF parser integration), see the updates section in the system design rationale documentation at [`docs/architecture.md#12-late-2026-codebase-updates--clean-up`](docs/architecture.md#12-late-2026-codebase-updates--clean-up).



## What's genuinely verified vs. what still needs a live check

Every file in this repo compiles cleanly and the full 156-test suite passes
against the assembled tree with real dependencies installed — that's been
run, not just claimed. What has **not** been run against live infrastructure:
- Any real WhatsApp send/receive, including the tap-to-confirm Flow
  (`send_flow()`'s payload shape is a best-effort implementation of Meta's
  documented format, unverified against a live WABA — see its own docstring)
- Sarvam Vision's actual product-photo scope (vs. document/OCR-only)
- Flux Pro's exact endpoint/payload shape
- The Agmarknet resource ID/response schema

Each of these fails safe (falls through to a free/local tier or a friendly
Bengali error) rather than crashing if wrong — but "fails safe" isn't the
same as "confirmed working." Treat this as engineering-complete,
staging-ready, not field-tested.

## Repository layout

```
services/
  gateway/             FastAPI WhatsApp webhook + request boundary
                        whatsapp_flows/: scheme_eligibility_flow.json,
                        ledger_confirm_flow.json (tap-to-confirm ledger entries)
  orchestrator/         LangGraph state machine, feature nodes, model router
                         (Sarvam -> local Ollama cascade, no OpenAI)
    nodes/
      pricing_node.py       Pricing Recommendation agent — deterministic core
      negotiation_node.py   Negotiation agent — code-enforced price floor +
                             deterministic tactic selection
      price_chat_node.py    Friend-style seller pricing chat, pre-poster
      ledger_confirm_flow_node.py   Tap-to-confirm Flow consumer
      cross_verify.py       Independent second-pass dignity/numeric check
      scheme_rag_node.py    Hallucination-guarded scheme Q&A (not routed)
  rag_service/           Hybrid retrieval + per-chunk grounding verifier
  translation_service/  Sarvam client (chat, vision, translate, self-hosted fallback)
  voice_gateway/         Saaras V3 -> self-hosted faster-whisper STT cascade
  pdf_service/           Bank-submittable monthly report generation (continuity,
                          SHG grading, declaration + sign-off line)
  vision_service/        Catalog image processing, dual captions, ad-poster composite
                          (flux_poster_client.py: optional Flux Pro tier;
                           poster_composer.py: free Pillow tier, always available)
  market_service/        k-anonymized market trend aggregation + Agmarknet client
shared/
  config/ db/ observability/ storage/ whatsapp/
  knowledge/            Shared cultural/market context: statewide festivals, district
                         melas, life-cycle occasions (Hindu/Muslim/Christian Bengali),
                         crop sowing/harvest calendar, negotiation tactics, dignity
                         rules — the single source every agent reads from
                         (docs/architecture.md §10)
  i18n/                 Bengali calendar + centralized Bengali digit/number-word helpers
  catalog/               West Bengal SHG product taxonomy (papad, Kantha, etc.)
scripts/
  seed_schemes.py        Real PDF-to-chunk-to-embedding seeding pipeline for Scheme
                          RAG — requires a human-written manifest.json, never guesses
                          scheme content (see data/schemes/raw/README.md)
data/schemes/raw/        Where you place official government scheme PDFs — ships
                          empty on purpose, see that directory's README
assets/fonts/          Bengali TTF for poster text overlay (you provide the file)
migrations/            Init SQL + additive migrations, applied automatically on first boot
tests/unit/            156 fast, offline tests — security-critical logic, pricing,
                        knowledge-base, and scheme-seeding-chunking coverage
```

## License

AGPLv3 — see `LICENSE`.
