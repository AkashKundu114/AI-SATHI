# Known Issues and Development Roadmap

This document tracks known operational constraints, pending real-world validations, recently resolved issues, and the active development roadmap for AI-SATHI.

## Operational Constraints

- **Local Fallback Resource Usage**: Running self-hosted Ollama and faster-whisper fallbacks requires significant system memory and dedicated VRAM. In lightweight production deployments (such as single-container Azure hosts), relying on the primary Sarvam AI API with graceful error messaging is standard practice.
- **Azure SAS Token Expiry**: Shared Access Signature (SAS) tokens generated for WhatsApp outbound media links have a 1-hour validity window. Client applications displaying these assets should request updated URLs when tokens expire.
- **Deduplication Storage Retention**: Webhook deduplication records and rate limit counters are stored in PostgreSQL (`webhook_dedup` and `rate_limit_counters`). Operators should set up a weekly maintenance job to run `backend/scripts/cleanup_dedup.py` or execute an equivalent SQL query to remove records older than seven days.

## Recently Resolved

- **Duplicate Onboarding Records**: Resolved an issue where users entering phone numbers with varied formats (such as with or without a `+91` country code) could produce duplicate profiles. Phone numbers are now normalized before lookup and creation, with safe rollbacks on conflict.
- **Voice Chat Route Alias**: Added `/api/chat/voice` with multipart audio parsing so browser microphone recordings can be sent directly to the speech-to-text pipeline.
- **Unified JWT Secret Resolution**: Resolved occasional 401 signature mismatches between the gateway auth router and internal token validators.
- **Browser Chat Persistence**: Added `localStorage` message history to the React web UI, preventing lost draft messages on browser reload, along with an explicit chat reset button.
- **Docker Compose Database Override**: Added support for overriding `DATABASE_URL` directly via environment variables without editing compose files.

## Pending Field Validation

The following items are functional in the test suite but require continued monitoring under live rural conditions:

- **WhatsApp Flows Tap-to-Confirm**: Validating interactive button and form behavior under low-bandwidth 2G and 3G cellular connections.
- **Document OCR Variety**: Evaluating Sarvam Document Intelligence (`Parse`) across handwritten Bengali receipts, torn bills, and varied passbook layouts.
- **Commodity Price Feeds**: Verifying real-time API response formats from state Agmarknet market data endpoints for rural produce centers.

## Active Roadmap

1. **Agricultural Diagnostics**: Work on pest and crop disease detection is currently paused while we collect and verify localized regional crop image datasets with district agricultural extension offices.
2. **Multi-Speaker Meeting Diarization**: Exploring speaker diarization models to help SHG leaders automatically capture minutes and loan disbursements during weekly group meetings.
3. **Government Scheme Retrieval Expansion**: Expanding the RAG knowledge base with updated West Bengal state social schemes and district-specific subsidies.
