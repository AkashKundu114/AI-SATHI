# Test Fixtures

Fixtures here are small, deterministic inputs for offline tests.

- `sample_*_webhook.json` files mirror WhatsApp Cloud API webhook payloads.
- `audio/` and `images/` are reserved for tiny media samples if a future test
  needs real bytes. Prefer generating media inside tests when possible.

Do not commit large real user media or production webhook payloads.
