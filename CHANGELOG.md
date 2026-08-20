# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-08-20

### Added
- **Sarvam AI exclusive stack**: `saaras:v4`, `mayura:v1`, `sarvam-105b`, `sarvam-105b-conversations`, `Parse`, `Vision`
- **Multi-turn Bengali context**: Conversation state tracks last discussed/rejected ledger entries for correction flow
- **Bengali dialect support**: Handles local product slang (e.g., sorser tel = mustard oil) with contextual continuation
- **390-test suite**: Full offline coverage for security, edge cases, and behavioral validation
- **Red team / blue team / pen test audit**: Documented in `docs/red-team.md` Section 12
- **SVG architecture diagrams**: System architecture, app flow, and Sarvam model stack in `docs/assets/`
- **JWT Authentication**: Enterprise-grade JWT auth in API Gateway
- **IDOR Protection**: Strict token-subject matching on `/ledger` and `/storage/documents`
- **GitHub Actions CI/CD**: Test + lint pipeline and GHCR deploy workflow

### Changed
- **Model router simplified**: Single direct Sarvam call instead of multi-model cascade loop
- **Confirmation flow separation**: Clean routing for affirmative/negative/correction responses
- **Codebase cleanup**: Comments stripped, em-dashes normalized, stale files removed
- **Repository restructured**: Removed duplicate `services/`, `scripts/` shims; fixed Makefile and Docker paths

### Removed
- **OpenAI dependency**: Entirely removed in favor of Sarvam AI + local Ollama fallback
- **Bulbul TTS**: No text-to-speech - voice notes only via `saaras:v4`

## [1.0.0] - 2026-08-01

### Added
- Initial release with voice ledger, catalog creator, pricing, negotiation, market predictor
- LangGraph state machine with PostgreSQL checkpointing
- WhatsApp Cloud API integration
- Self-hosted Ollama + faster-whisper fallback tier
