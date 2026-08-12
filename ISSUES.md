# Known Issues & Roadmap

This document outlines known issues, architectural limitations, and roadmap items for the AI-SATHI project.

## Known Security Considerations
- **Open Red Team Findings**: Ensure all Red Team report findings (from `docs/red-team.md`) not yet addressed are tracked and prioritized. 
- **Blob SAS Lifetime**: SAS tokens generated via `generate_blob_sas_url` are time-bound to 1 hour. Front-end clients must implement logic to gracefully refresh them upon expiry to maintain uninterrupted document viewing.

## Architectural Limitations
- **Ollama Hardware Requirements**: The local fallback model (Ollama) requires adequate VRAM/RAM on self-hosted environments. In production, ensure fallback nodes have sufficient resources to handle concurrent processing during Sarvam AI API outages.
- **PostgreSQL Rate Limit & Dedup Bloat**: A cleanup script (`scripts/cleanup_postgres_retention.sql`) has been provided to clear out deduplication cache records older than 7 days, but this requires a cron-job setup to execute regularly on the production server.

## Feature Roadmap
1. **Agri-Diagnostics Module**: Currently paused. Vision models require more localized agriculture datasets specifically tuned for West Bengal crops before enabling live pest diagnostics.
2. **Meeting Minutes Module**: Speech-to-text context windows and speaker diarization for multi-speaker SHG meetings remain experimental and are slated for a future release once the core ledger logic has proven stable in the field.
3. **Subsidy Matchmaking**: Grounding verifications for scheme documents are in place via the Scheme RAG (Retrieval-Augmented Generation), but chat routing directly to these documents is not yet activated by default.
