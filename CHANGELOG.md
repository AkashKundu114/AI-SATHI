# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-08-26

### Added
- **Browser Chat Persistence**: Saved ongoing chat conversations in browser `localStorage` so sessions survive page refreshes, and added a manual "Reset Chat" action.
- **Voice Chat Route**: Added `/api/chat/voice` endpoint alias with multipart audio support for direct in-browser voice note recording.
- **User Authentication**: Added user registration and login endpoints with PBKDF2 password hashing, plus fallback credential handling for local testing.
- **Profile Fields**: Added structured user profile fields for district, state, business name, and business category.
- **Docker Compose Override**: Enabled overriding `DATABASE_URL` through environment variables in `docker-compose.yml` for flexible local setups.
- **Paper Export Tooling**: Added `md-to-pdf` and Puppeteer tooling for compiling project documentation and whitepapers.

### Changed
- **LangGraph Checkpointer**: Switched conversation state persistence to use native PostgreSQL checkpointing for resumable multi-turn dialogues.
- **Frontend Delivery**: Configured single-container static build serving so the React web UI is served directly alongside the FastAPI gateway.
- **Phone Lookup Matching**: Expanded database phone lookup to match multiple common Indian formats, including `+91` prefixes and 10-digit variants.

### Fixed
- **JWT Secret Resolution**: Unified JWT secret key handling across all gateway endpoints to prevent 401 signature mismatches between services.
- **Session Expiration**: Added graceful handling for 401 responses on the frontend, clearing stale tokens and redirecting cleanly to login.
- **Duplicate Onboarding**: Normalized phone numbers before creating new records to avoid duplicate user accounts when the same number is entered differently.
- **Profile Routing**: Refactored post-profile routing in the state machine so new user onboarding and confirmation flows do not collide.
- **Ledger Item Mapping**: Improved item name and unit price extraction for mixed Bengali and Banglish transaction terms.
- **Image Validation**: Added file completeness and dimension checks in the gateway before handing images to the vision processing pipeline.

## [2.0.0] - 2026-08-20

### Added
- **Sarvam AI Indic Models**: Integrated official Sarvam models (`saaras:v4` for STT, `mayura:v1` for translation, `sarvam-105b` for entity extraction, `sarvam-105b-conversations` for dialogue, `Parse` for document OCR, and `Vision` for catalog images).
- **LangGraph State Machine**: Implemented stateful graph orchestration with multi-turn context tracking for correcting ledger entries.
- **Offline Test Suite**: Built an offline test suite of 390 unit and integration tests covering security, edge cases, and arithmetic validation without live API keys.
- **Security Audit Coverage**: Documented red team and blue team penetration testing results in `docs/red-team.md` and `docs/security.md`.
- **Architecture Visuals**: Added SVG diagrams for overall architecture, application flow, and the Sarvam model stack.
- **Access Control**: Added JWT authentication in the API Gateway and enforced object-level permissions on ledger endpoints.

### Changed
- **Model Routing**: Replaced cascading loops with direct Sarvam API calls managed through `model_router.py` with circuit breakers and timeouts.
- **Confirmation Flow**: Separated confirmation handling into distinct affirmative, negative, and correction logic paths.
- **Architecture Simplification**: Replaced Celery workers and Redis with in-process FastAPI background tasks and PostgreSQL deduplication tables.
- **Code Organization**: Cleaned up legacy service shims, standardized documentation, and updated Docker configurations.

### Removed
- **OpenAI Dependency**: Phased out OpenAI models in favor of Sarvam AI and optional local Ollama instances.
- **Legacy TTS**: Removed Bulbul Text-to-Speech; voice processing now centers on `saaras:v4`.
- **Redis and MinIO**: Removed Redis and MinIO services in favor of PostgreSQL and Azure Blob Storage.

## [1.0.0] - 2026-08-01

### Added
- Initial release of the voice ledger, automated catalog builder, algorithmic pricing rules, negotiation helper, and market trend predictor.
- Implemented LangGraph state machine with PostgreSQL checkpoint persistence.
- Integrated Meta WhatsApp Cloud API for voice note and text messaging.
- Set up local faster-whisper and Ollama fallback options for offline environments.

[2.1.0]: https://github.com/AkashKundu114/AI-SATHI/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/AkashKundu114/AI-SATHI/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/AkashKundu114/AI-SATHI/releases/tag/v1.0.0
