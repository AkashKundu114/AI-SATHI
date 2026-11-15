# AI-SATHI Documentation

Welcome to the technical documentation for AI-SATHI. This directory contains detailed guides covering system architecture, product requirements, security audits, verification testing, and operational runbooks.

## Documentation Index

| Document | Purpose |
|---|---|
| [**architecture.md**](architecture.md) | Architectural decisions, LangGraph state machine, Sarvam Indic AI model routing, PostgreSQL persistence, and single-container deployment details. |
| [**product.md**](product.md) | Product requirements, user personas, transaction categories, and conversational flow definitions. |
| [**engineering-review.md**](engineering-review.md) | Review checklist covering code invariants, test expectations, and system handover audits. |
| [**security.md**](security.md) | Security design, JWT authentication, rate limiting, HMAC-SHA256 webhook validation, input sanitization, and PII masking. |
| [**red-team.md**](red-team.md) | Adversarial testing, dialect prompt injection defenses, balance overflow protections, and penetration test verification. |
| [**runbooks/restore.md**](runbooks/restore.md) | Operational procedures for restoring PostgreSQL from Blob Storage backups and disaster recovery drills. |

## Quick Start Configuration

```bash
cd AI-SATHI
cp .env.example .env          # Configure database, Sarvam API key, and secrets
docker compose up --build -d   # Start the application stack
```

Access the web interface at `http://localhost:8000/`. Default administrative credentials are `admin` / `admin`.

## Releases and Tags

Detailed changelog notes and repository release tags are documented in the root [CHANGELOG.md](../CHANGELOG.md):

- **v2.1.0** (2026-08-26): Web UI chat persistence, PBKDF2 authentication, `/api/chat/voice` endpoint, database URL override, and documentation export tooling.
- **v2.0.0** (2026-08-20): Full Sarvam AI model migration, LangGraph state machine, PostgreSQL checkpointer, 390 offline tests, and Azure deployment.
- **v1.0.0** (2026-08-01): Initial prototype release with WhatsApp voice ledger, catalog generation, and rule-based pricing.

## Visual Architecture References

- **Overall System Architecture**: [assets/architecture_diagram.svg](assets/architecture_diagram.svg)
- **Application Flow and State Transitions**: [assets/app_flow_diagram.svg](assets/app_flow_diagram.svg)
- **Sarvam AI Integration Layer**: [assets/sarvam_middleman_stack.svg](assets/sarvam_middleman_stack.svg)
