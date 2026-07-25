# Cost Model

Kotha-Khata keeps paid-vendor surface area small: Sarvam is the primary AI
vendor, Flux is optional for poster generation, and all core services can run
on a single Docker host for small deployments.

## AI Cascade

| Workload | Paid tier | Free fallback |
|---|---|---|
| Ledger extraction and correction | Sarvam `sarvam-30b` | local Ollama `qwen2.5` |
| Intent routing and general conversation | Sarvam `sarvam-30b` | local Ollama `qwen2.5` |
| Pricing and market phrasing | Sarvam `sarvam-30b` | local Ollama `qwen2.5` |
| Ads, negotiation, stronger phrasing | Sarvam `sarvam-105b` | local Ollama `qwen2.5` |
| Product photo analysis | Sarvam Vision | local Ollama `qwen2-vl` |
| Translation / Banglish normalization | Sarvam translate | self-hosted translate endpoint, then Ollama |
| Speech-to-text | Saaras V3 | faster-whisper |
| Poster generation | Flux Pro, optional | local Pillow composer |

## Required Cost Controls

- Set a Sarvam dashboard spend cap before production traffic.
- Keep `MAX_MESSAGES_PER_HOUR` conservative for the pilot.
- Enable `USE_LOCAL_MODELS=true` if uptime matters during Sarvam outages.
- Leave `FLUX_API_KEY` blank unless image-generation spend is approved.
- Monitor model usage by `model_used` in node traces or logs.

## Cost-Saving Design Choices

- Ledger, pricing, and negotiation numbers are computed in code.
- Translation calls only run when a cheap local heuristic sees code-mixed text.
- Catalog poster generation has a free local Pillow path.
- Market prediction uses local database aggregation before model phrasing.
- The off-topic conversation node only runs after normal routing fails.

## Budget Risks

- A popular catalog feature can drive Flux spend quickly if enabled.
- Sarvam outages without local fallback become availability incidents, not just
  cost events.
- More WhatsApp users increase media storage and egress costs.
- Long audio messages are expensive; keep media caps enforced.
