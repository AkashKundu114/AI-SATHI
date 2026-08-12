# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **JWT Authentication**: Implemented enterprise-grade JWT-based authentication in API Gateway (`api_router.py`), replacing legacy hardcoded administrative keys.
- **IDOR Protection**: Secured `/ledger`, `/ledger/confirm`, and `/storage/documents` with strict explicit token-subject matching.
- **SAS URL Generation**: Dynamic Time-Limited SAS URL generation for Azure Blob Storage in `azure_client.py` and document endpoints to prevent unauthorized blob access (Red Team 11.3).
- **Retention Scripts**: Created `scripts/cleanup_postgres_retention.sql` for truncating outdated deduplication payloads and managing DB bloat (Red Team 11.1).

### Changed
- **Exception Handling**: Removed overly broad `except Exception:` catches in favor of explicit `SQLAlchemyError` catches with safe logging across the router and LangGraph nodes.
- **Ledger Commit Bounds**: Strengthened upper-bounds checks (`MAX_REASONABLE_AMOUNT`) during confirmation steps (Red Team High-4).
- **Code Quality**: Applied complete `-> dict` type-hinting and detailed docstring structures to API Gateway endpoints as per Microsoft Code Quality practices.
- **Documentation**: Revamped `README.md` to highlight the production readiness and Google XYZ impact formula statement.

### Removed
- **OpenAI Fallbacks**: Entirely removed the OpenAI fallback tier from the orchestrator in favor of self-hosted local Ollama implementations to strictly comply with budget and privacy designs.
