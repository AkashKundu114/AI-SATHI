# Known Issues & Roadmap

## Known Limitations

- **Ollama VRAM**: Local fallback requires adequate VRAM/RAM. Ensure fallback nodes have sufficient resources for concurrent processing during Sarvam API outages.
- **Blob SAS Lifetime**: Azure SAS tokens are time-bound to 1 hour. Frontend clients must handle refresh on expiry.
- **Dedup Cache Bloat**: Run `backend/scripts/cleanup_dedup.py` or the SQL script on a cron schedule to clear records older than 7 days.

## Not Yet Live-Tested

- Real WhatsApp send/receive (including tap-to-confirm Flow)
- Sarvam Vision product-photo scope (vs. document/OCR)
- Flux Pro endpoint/payload shape
- Agmarknet resource ID/response schema

Each fails safe (falls to free/local tier or friendly Bengali error) rather than crashing.

## Feature Roadmap

1. **Agri-Diagnostics**: Paused - needs localized West Bengal crop datasets for pest diagnostics
2. **Meeting Minutes**: Multi-speaker diarization for SHG meetings - experimental, future release
3. **Subsidy Matchmaking**: RAG grounding in place, chat routing not yet activated by default
