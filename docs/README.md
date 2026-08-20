# AI-SATHI Documentation

Comprehensive documentation for the AI-SATHI v2.0 production release.

## Index

| Document | Description |
|---|---|
| [**architecture.md**](architecture.md) | System architecture - LangGraph FSM, Sarvam AI middleman stack, PostgreSQL + pgvector, Docker containerization |
| [**product.md**](product.md) | Product requirements - 8 Bengali/Banglish transaction modes, conversational separation, onboarding flows |
| [**engineering-review.md**](engineering-review.md) | Engineering audit - 390-test suite pass, PostgreSQL tuning, container optimizations |
| [**security.md**](security.md) | Security architecture - JWT auth, rate limiting, HMAC-SHA256 validation, input sanitization, PII masking |
| [**red-team.md**](red-team.md) | Adversarial audit - dialect edge cases, prompt injection, balance overflow, pen test results |
| [**runbooks/restore.md**](runbooks/restore.md) | Operations - PostgreSQL backup/restore, Docker recovery, migration runbooks |

## Quick Start

```bash
cd AI-SATHI
cp .env.example .env        # Configure credentials
docker compose up --build -d # Launch full stack
```

App: `http://localhost:8000/` - Default login: `admin` / `admin`

## Architecture

![System Architecture](assets/architecture_diagram.svg)

## Application Flow

![App Flow](assets/app_flow_diagram.svg)

## Sarvam AI Model Stack

![Sarvam Model Stack](assets/sarvam_middleman_stack.svg)
