# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2026-08-20

### Added
- **Sarvam AI Integration**: Deployed \saaras:v4\, \mayura:v1\, \sarvam-105b\, \sarvam-105b-conversations\, \Parse\, and \Vision\ models.
- **Conversational State Management**: Implemented multi-turn context tracking for ledger entry correction workflows.
- **Dialect Processing**: Added robust support for regional product terminology and contextual interpretation.
- **Comprehensive Testing**: Integrated a 390-test offline suite for security, edge cases, and behavioral validation.
- **Security Audits**: Completed and documented red team/blue team penetration testing in \docs/red-team.md\.
- **System Documentation**: Added scalable vector graphics (SVG) for architecture and data flow diagrams.
- **Authentication**: Implemented JWT authentication within the API Gateway.
- **Access Control**: Enforced strict Insecure Direct Object Reference (IDOR) protection on critical endpoints.
- **CI/CD Pipeline**: Configured GitHub Actions for automated testing, linting, and container registry deployment.

### Changed
- **Model Routing**: Consolidated cascading loops into direct Sarvam API calls for improved latency.
- **Flow Control**: Separated confirmation flows to distinctly handle affirmative, negative, and correction responses.
- **Code Quality**: Normalized documentation, stripped extraneous comments, and removed deprecated files.
- **Repository Structure**: Resolved duplicate service shims and corrected Makefile/Docker configurations.

### Removed
- **OpenAI Dependency**: Phased out completely in favor of Sarvam AI and localized Ollama instances.
- **Legacy TTS**: Removed Bulbul Text-to-Speech service; voice notes are now handled exclusively via \saaras:v4\.

## [1.0.0] - 2026-08-01

### Added
- Initial deployment of voice ledger, catalog creation, algorithmic pricing, negotiation engine, and market predictor.
- Implemented LangGraph state machine with PostgreSQL checkpoint persistence.
- Integrated WhatsApp Cloud API for external messaging.
- Provisioned self-hosted Ollama and faster-whisper as a secondary fallback tier.
