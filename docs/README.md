# AI-SATHI Documentation & Handover Guide

Welcome to the **AI-SATHI v2 (Late-2026 Production Release)** documentation repository. AI-SATHI is an AI-powered conversational operating system and financial ledger designed for rural micro-entrepreneurs and Self-Help Groups (SHGs) across West Bengal and India.

---

## 📑 Core Documentation Index

| Document | Purpose |
|---|---|
| [`architecture.md`](architecture.md) | **Comprehensive System Architecture**: LangGraph FSM, Sarvam AI Middleman (`saaras:v4`, `mayura:v1`, `sarvam-105b`, `sarvam-105b-conversations`, `Parse`, `Vision`), PostgreSQL + pgvector storage, and Docker containerization. (See §13 for latest updates). |
| [`product.md`](product.md) | **Product Requirements & Specifications**: 8 Bengali/Banglish transaction modes, zero-interference conversational separation, user onboarding flows, and visual catalog generation. |
| [`engineering-review.md`](engineering-review.md) | **Engineering Audit & Verification**: Complete test suite pass (`389 passed`), PostgreSQL performance tuning, and low-cost container optimizations. |
| [`security.md`](security.md) | **Security Architecture**: JWT auth, rate limiting, HMAC-SHA256 WhatsApp signature validation, input sanitization, and PII masking. |
| [`red-team.md`](red-team.md) | **Adversarial Audit**: Boundary testing on dialect edge cases, prompt injections, and balance overflow guards. |
| [`runbooks/restore.md`](runbooks/restore.md) | **Operations & Disaster Recovery**: PostgreSQL backup/restore, Docker stack recovery, and database migration runbooks. |

---

## 🚀 Quick Start (Docker Deployment)

The entire AI-SATHI stack is containerized with zero local software dependencies (aside from Docker Desktop):

```bash
# 1. Clone the repository and navigate to root
cd AI-SATHI

# 2. Configure environment variables (optional, defaults provided)
cp .env.example .env

# 3. Build and launch all services via Docker Compose
docker compose up --build -d app postgres azurite

# 4. Check running containers
docker compose ps
```

The application is immediately accessible at **`http://localhost:8000/`**.
Default Admin Login: Username: `admin` | Password: `admin` (maps to phone `9064349004`).

---

## 🏛️ System Architecture

![AI-SATHI System Architecture](assets/architecture_diagram.svg)

---

## 🔄 End-to-End Application & Decision Flow

![AI-SATHI App Flow Diagram](assets/app_flow_diagram.svg)

---

## 🧠 Sarvam AI Middleman Model Stack

![Sarvam AI Model Stack](assets/sarvam_middleman_stack.svg)

