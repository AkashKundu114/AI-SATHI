# Known Issues and Development Roadmap

## System Limitations

- **Resource Constraints (Ollama VRAM)**: The localized fallback tier requires substantial VRAM/RAM allocation. System administrators must ensure fallback nodes are adequately provisioned to handle concurrent processing during primary API outages.
- **Token Expiration (Azure SAS)**: Azure Shared Access Signatures (SAS) are constrained to a one-hour lifetime. Client applications must implement robust token refresh mechanisms upon expiration.
- **Data Retention (Deduplication Cache)**: To prevent storage bloat, operators should configure a cron schedule to execute \ackend/scripts/cleanup_dedup.py\ or the equivalent SQL script, purging records exceeding a seven-day threshold.

## Pending Validation

The following components require final live-environment validation:

- Real-world WhatsApp transmission and reception, including tap-to-confirm Flow interactions.
- Scope limitations for Sarvam Vision processing on product photography versus document OCR.
- Verification of the Flux Pro endpoint behavior and payload structures.
- Schema validation for Agmarknet resource identifiers and API responses.

*Note: All unverified components are engineered to fail gracefully, defaulting to secondary tiers or localized error handling to prevent systemic crashes.*

## Development Roadmap

1. **Agricultural Diagnostics**: Development paused pending acquisition of localized regional crop datasets for accurate pest diagnostics.
2. **Meeting Transcription**: Integration of multi-speaker diarization for group meetings is slated for experimental testing in a future release.
3. **Subsidy Allocation Module**: RAG grounding is fully implemented; however, chat routing logic is currently disabled by default pending further review.
