# AI-SATHI

**Enterprise Voice-First Financial Assistant**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#) [![License](https://img.shields.io/badge/license-AGPL--3.0-blue)](#) [![Python Version](https://img.shields.io/badge/python-3.11-blue)](#) [![React](https://img.shields.io/badge/react-18-blue)](#)

## Executive Summary

AI-SATHI is a production-grade, voice-first Web UI financial assistant designed for Self-Help Group (SHG) micro-entrepreneurs. It processes regional voice inputs into structured financial ledgers, generates compliance-ready PDF reports, automates catalog creation, and provides predictive market trend analysis. The system is engineered for high availability and is hosted on Microsoft Azure via GCP pipelines, accessible securely through kothakhata.app.

### Core Capabilities

- **Web-Native Interface**: Interactive React and Vite frontend accessible directly via standard web browsers.
- **Dedicated AI Infrastructure**: Operates independently of standard OpenAI dependencies, utilizing saaras:v4, mayura:v1, sarvam-105b, sarvam-105b-conversations, Parse, and Vision.
- **Advanced Voice Intelligence**: Multi-lingual Speech-to-Text (STT) and Text-to-Speech (TTS) utilizing faster-whisper and region-specific acoustic models.
- **Robust Quality Assurance**: Backed by a comprehensive 390-test offline suite ensuring security, edge-case coverage, and behavioral consistency under constrained network conditions.

## System Architecture

The core architecture operates via a centralized API gateway (`backend/services/gateway`) built on FastAPI. This layer manages web session authentication, request deduplication, and rate-limiting. Workloads are dispatched to the orchestrator (`backend/services/orchestrator`), a LangGraph state machine with PostgreSQL checkpointing for resumability.

Model interactions are routed exclusively through `backend/services/orchestrator/model_router.py`, establishing a resilient cascade with automated retries and strict timeouts. Contextual domain knowledge is centralized in `backend/shared/knowledge/`, ensuring consistent logic across all autonomous agents.

## Feature Specifications

| Component | Technical Description |
|---|---|
| **Voice Ledger** | End-to-end pipeline for voice note ingestion, structured data extraction, confirmation loops, transactional database writes, and PDF generation. |
| **Catalog Automation** | Image processing pipeline incorporating background removal, computer vision identification, dual-language caption generation, dynamic pricing calculation, and ad composite generation. |
| **Conversational Pricing** | State-driven dialog system designed to establish pricing consensus prior to poster generation. |
| **Algorithmic Pricing** | Deterministic floor-pricing calculations based on cost margins, producing natural language outputs without unstructured generation of numerical values. |
| **Negotiation Engine** | Rule-based engine enforcing price floors, computing deterministic counter-offers, and implementing post-generation safety scans. |
| **Market Predictor** | Aggregation of k-anonymized ledger data and external market datasets for predictive trend analysis. |
| **Contextual RAG** | Retrieval-Augmented Generation subsystem featuring hallucination guardrails and per-chunk grounding verification. |
| **Cross-Agent Verification** | Secondary independent validation layer for numerical accuracy and compliance on critical transactional messages. |

## Quick Start Guide

### Initialization

```bash
git clone https://github.com/AkashKundu114/AI-SATHI.git
cd AI-SATHI
cp .env.example .env
```

Ensure `.env` is populated with the requisite SARVAM_API_KEY and WhatsApp API credentials.

### Deployment

```bash
docker compose up --build -d
```

The application will bind to `http://localhost:8000`. Default administrative credentials are `admin` / `admin`.

### Infrastructure Requirements

- **Containerization**: Docker and Docker Compose for local development and deployment.
- **Hosting**: Microsoft Azure Virtual Machine for production environments.
- **CI/CD**: GitHub Actions for automated testing and deployment workflows.
- **AI Services**: Sarvam AI API access.
- **Fallback Services**: Local Ollama instance (optional but recommended for API resilience).

## Repository Architecture

```text
AI-SATHI/
├── backend/
│   ├── services/
│   │   ├── gateway/              # FastAPI webhook receiver and Flow handlers
│   │   ├── orchestrator/         # LangGraph state machine and model routing
│   │   ├── translation_service/  # External API client operations
│   │   ├── voice_gateway/        # STT cascade integration
│   │   ├── pdf_service/          # Automated report generation
│   │   ├── vision_service/       # Image processing pipeline
│   │   ├── rag_service/          # Hybrid retrieval and grounding verification
│   │   └── market_service/       # Data aggregation and trend analysis
│   ├── shared/
│   │   ├── config/               # Application configuration and token limits
│   │   ├── db/                   # SQLAlchemy ORM and session handlers
│   │   ├── guardrails/           # Input/output validation and caching
│   │   ├── i18n/                 # Localization and formatting utilities
│   │   ├── knowledge/            # Centralized domain knowledge
│   │   └── security/             # Audit logging and input sanitization
│   └── scripts/                  # Administrative and maintenance tools
├── frontend/                     # React and Vite SPA
├── migrations/                   # PostgreSQL schema migrations
├── tests/                        # Unit and integration test suites
└── docs/                         # Technical documentation and runbooks
```

## Testing Protocol

The repository includes a comprehensive, offline-capable test suite.

```bash
# Execute full test suite
python -m pytest tests/ -q

# Execute rapid smoke tests
make test-fast

# Generate coverage report
python -m pytest tests/ --cov=shared --cov-report=term
```

## Documentation Reference

- [docs/architecture.md](docs/architecture.md): Detailed system design and deployment architecture.
- [docs/product.md](docs/product.md): Product specifications and transaction mode definitions.
- [docs/engineering-review.md](docs/engineering-review.md): Security audits, performance tuning, and test coverage analysis.
- [docs/security.md](docs/security.md): Authentication protocols, rate limiting, and data masking specifications.
- [docs/red-team.md](docs/red-team.md): Adversarial testing and edge-case mitigation strategies.
- [docs/runbooks/restore.md](docs/runbooks/restore.md): Disaster recovery and operational runbooks.

## Technology Stack

- **Application Layer**: Python 3.11, FastAPI, Uvicorn, React, Vite
- **Data Persistence**: PostgreSQL 16, pgvector
- **State Management**: LangGraph
- **AI Infrastructure**: Sarvam AI, Ollama, faster-whisper
- **External Integration**: Meta WhatsApp Cloud API
- **Deployment**: Docker Compose, Caddy, GitHub Actions

## Contributing

We welcome contributions from the community. Please refer to our contributing guidelines before submitting a pull request. Ensure that all tests pass locally and that new features include appropriate test coverage.

## Licensing

Licensed under the AGPL-3.0 License. Refer to [LICENSE](LICENSE) for details.
