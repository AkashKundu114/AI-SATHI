# AI-SATHI Technical Documentation

This directory contains the comprehensive technical documentation for the AI-SATHI v2.0 production deployment.

## Documentation Index

| Document | Description |
|---|---|
| [**architecture.md**](architecture.md) | System architecture detailing the LangGraph FSM, Sarvam AI routing stack, PostgreSQL/pgvector integration, and Docker containerization. |
| [**product.md**](product.md) | Product specifications defining the eight transaction modes, conversational routing, and user onboarding logic. |
| [**engineering-review.md**](engineering-review.md) | Engineering audit covering test suite validation, PostgreSQL performance tuning, and infrastructure optimizations. |
| [**security.md**](security.md) | Security architecture outlining JWT authentication, rate limiting, HMAC-SHA256 validation, input sanitization, and PII masking. |
| [**red-team.md**](red-team.md) | Adversarial audit documenting dialect edge cases, prompt injection defense, balance overflow protections, and penetration testing results. |
| [**runbooks/restore.md**](runbooks/restore.md) | Operational procedures including PostgreSQL backup and restoration, Docker recovery, and database migration guidelines. |

## Quick Start Configuration

`ash
cd AI-SATHI
cp .env.example .env        # Configure necessary credentials
docker compose up --build -d # Initialize the application stack
`

Access the application at \http://localhost:8000/\. Default administrative credentials are \dmin\ / \dmin\.

## System Architecture

![System Architecture](assets/architecture_diagram.svg)

## Application Flow

![App Flow](assets/app_flow_diagram.svg)

## Sarvam AI Model Stack

![Sarvam Model Stack](assets/sarvam_middleman_stack.svg)
