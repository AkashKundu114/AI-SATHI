# AI-SATHI

**Voice-First Financial Assistant for Rural Micro-Entrepreneurs**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)
[![Release](https://img.shields.io/badge/release-v2.1.0-blue)](https://github.com/AkashKundu114/AI-SATHI/releases/tag/v2.1.0)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.11-blue)](#)
[![React](https://img.shields.io/badge/react-18-blue)](#)

## Overview

AI-SATHI is an open-source, voice-first financial assistant created for Self-Help Group (SHG) micro-entrepreneurs. It turns everyday spoken Bengali and regional dialects into structured accounting records, generates shareable product catalogs, produces compliance-ready PDF summaries, and calculates pricing guidance based on actual costs.

Users can interact with the system through a responsive web app at kothakhata.app (with in-browser voice recording) or through WhatsApp Cloud API messaging.

### Key Capabilities

- **Dual-Channel Access**: Clean React 18 and Vite web app with microphone recording and local storage persistence, paired with WhatsApp Cloud API messaging.
- **Indic Language Processing**: Integrated with Sarvam AI models (`saaras:v4`, `mayura:v1`, `sarvam-105b`, `sarvam-105b-conversations`, `Parse`, and `Vision`), with local faster-whisper and Ollama fallback options.
- **Guarded Financial Calculation**: All figures, totals, and profit margins are calculated deterministically in code; the language model is never allowed to invent numerical values.
- **Explicit Confirmation Loops**: Every transaction requires clear user confirmation before committing to the database. Cancellations discard cleanly with zero database writes.
- **Comprehensive Offline Tests**: 390 automated unit and integration tests covering security, dialect understanding, arithmetic edge cases, and network failure modes without live API keys.

## Releases and Repository Tags

| Tag | Date | Description | Changelog |
|---|---|---|---|
| [`v2.1.0`](https://github.com/AkashKundu114/AI-SATHI/releases/tag/v2.1.0) | 2026-08-26 | Web UI chat persistence, PBKDF2 auth, voice route alias, Docker Compose DB override, and paper export tooling. | [Details](CHANGELOG.md#210---2026-08-26) |
| [`v2.0.0`](https://github.com/AkashKundu114/AI-SATHI/releases/tag/v2.0.0) | 2026-08-20 | Sarvam AI migration, LangGraph state machine, PostgreSQL checkpointer, 390 offline tests, and single-container Azure deployment. | [Details](CHANGELOG.md#200---2026-08-20) |
| [`v1.0.0`](https://github.com/AkashKundu114/AI-SATHI/releases/tag/v1.0.0) | 2026-08-01 | Initial prototype release featuring WhatsApp voice ledger, catalog generation, pricing rules, and basic negotiation flow. | [Details](CHANGELOG.md#100---2026-08-01) |

To check out a specific release:

```bash
git fetch --tags
git checkout tags/v2.1.0
```

## System Architecture

The application runs as a unified service with three main tiers:

1. **API Gateway (`backend/services/gateway`)**: Built on FastAPI. Manages user registration and PBKDF2 login, validates JWT tokens, handles webhook deduplication via PostgreSQL, processes multipart audio uploads, and serves the static React frontend.
2. **Orchestrator (`backend/services/orchestrator`)**: A LangGraph state machine with PostgreSQL checkpoint persistence. Routes incoming intents, coordinates multi-turn ledger corrections, and runs background tasks without blocking webhooks.
3. **Model Router (`backend/services/orchestrator/model_router.py`)**: Directs external model requests to Sarvam AI, enforces per-task token limits, applies circuit breaking, and falls back to friendly localized messages if services are unavailable.

## Feature Breakdown

| Component | Function |
|---|---|
| **Voice Ledger** | Ingests spoken or written records, extracts structured items and prices, requests confirmation, writes to PostgreSQL, and generates downloadable PDF reports. |
| **Catalog Automation** | Takes product photos, removes backgrounds, identifies items, creates dual-language descriptions, and compiles ready-to-share image cards. |
| **Conversational Pricing** | Guides the seller through calculating fair floor prices based on material and labor costs before publishing advertisements. |
| **Deterministic Negotiation** | Applies hard cost floors to prevent underpricing, generates realistic counter-offers, and checks messages for numerical accuracy. |
| **Market Trend Insights** | Aggregates anonymized local sales records to show price trends across items, enforcing a minimum sample size of 5 distinct sellers for privacy. |
| **Grounded Scheme Search** | Uses retrieval-augmented search over government scheme documents with chunk verification to prevent false claims. |
| **Cross-Verification** | Secondary check on all financial calculations before user confirmation to catch discrepancy errors early. |

## Quick Start Guide

### 1. Clone and Configure

```bash
git clone https://github.com/AkashKundu114/AI-SATHI.git
cd AI-SATHI
cp .env.example .env
```

Open `.env` and fill in your configuration:
- `JWT_SECRET_KEY`: Long random string for session tokens.
- `SARVAM_API_KEY`: Your Sarvam AI platform API key.
- `DATABASE_URL`: Connection string for PostgreSQL (defaults to the docker-compose service).

### 2. Run with Docker Compose

```bash
docker compose up --build -d
```

The application starts at `http://localhost:8000`. Default administrative credentials are `admin` / `admin`.

### 3. Local Development (Without Docker)

Backend:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .[test]
uvicorn backend.services.gateway.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Repository Structure

```text
AI-SATHI/
├── backend/
│   ├── services/
│   │   ├── gateway/              # FastAPI endpoints, auth, webhooks, and static UI delivery
│   │   ├── orchestrator/         # LangGraph state machine, nodes, and model routing
│   │   ├── translation_service/  # Sarvam AI translation client
│   │   ├── voice_gateway/        # Speech-to-text handling and cascade fallbacks
│   │   ├── pdf_service/          # Ledger PDF report generation
│   │   ├── vision_service/       # Image cleanup and poster composition
│   │   ├── rag_service/          # Scheme document search and grounding checks
│   │   └── market_service/       # Price aggregation and market trend analysis
│   ├── shared/
│   │   ├── config/               # App configuration, limits, and token budgets
│   │   ├── db/                   # Database models, sessions, and deduplication
│   │   ├── guardrails/           # Financial input validation and rate limiting
│   │   ├── i18n/                 # Bengali calendar and number conversion utilities
│   │   ├── knowledge/            # Crop calendars and negotiation playbooks
│   │   └── security/             # Audit logs, input sanitation, and password hashing
│   └── scripts/                  # Database seeds, maintenance, and administrative scripts
├── frontend/                     # React 18, Vite, and Tailwind CSS web interface
├── migrations/                   # PostgreSQL schema migrations
├── tests/                        # 390 offline unit and integration tests
└── docs/                         # Technical documentation and operational runbooks
```

## Testing Protocol

The repository includes a 390-test offline suite that does not require network access or live API keys.

```bash
# Run the full offline test suite
python -m pytest tests/ -q

# Run quick smoke tests
make test-fast

# Run test suite with coverage report
python -m pytest tests/ --cov=shared --cov-report=term
```

## Documentation Reference

- [docs/architecture.md](docs/architecture.md): Architectural decisions, state management, and deployment considerations.
- [docs/product.md](docs/product.md): Product requirements, personas, transaction modes, and user journeys.
- [docs/engineering-review.md](docs/engineering-review.md): Invariants, test expectations, and system handover audits.
- [docs/security.md](docs/security.md): Authentication design, input sanitization, PII protection, and rate limiting.
- [docs/red-team.md](docs/red-team.md): Adversarial test findings, dialect prompt injection defenses, and pen-test verification.
- [docs/runbooks/restore.md](docs/runbooks/restore.md): Step-by-step procedures for database backups and disaster recovery.

## Technology Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy, Pydantic
- **Frontend**: React 18, Vite, Lucide React
- **Data Storage**: PostgreSQL 16, pgvector, Azure Blob Storage
- **Orchestration**: LangGraph state machine
- **Language Models**: Sarvam AI (`saaras:v4`, `mayura:v1`, `sarvam-105b`, `sarvam-105b-conversations`, `Parse`, `Vision`), faster-whisper, Ollama
- **Messaging**: Meta WhatsApp Cloud API
- **Deployment**: Docker Compose, Caddy, Azure Container Apps, GitHub Actions

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, code style expectations, testing steps, and release tagging workflows.

## Licensing

Distributed under the AGPL-3.0 License. See [LICENSE](LICENSE) for details.
