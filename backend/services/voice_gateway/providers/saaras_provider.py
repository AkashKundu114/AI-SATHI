from __future__ import annotations

import httpx

from shared.config.settings import get_settings

DOMAIN_PROMPT_HINT = "চাল, আলু, পেঁয়াজ, সরষে, ডাল, দেনা, বিয়োগ, হিসাব, স্বনির্ভর গোষ্ঠী, সিসিএল ঋণ, আনন্দধারা, তাগাদা, ইউপিআই"


async def transcribe(audio_bytes: bytes, language: str = "bn", prompt_hint: str | None = None) -> dict:
    s = get_settings()
    if not s.sarvam_api_key:
        raise RuntimeError("SARVAM_API_KEY not configured")

    lang_code = f"{language}-IN" if len(language) == 2 else language
    is_webm = audio_bytes.startswith(b"\x1a\x45\xdf\xa3") or b"webm" in audio_bytes[:100].lower()
    filename = "audio.webm" if is_webm else "audio.wav"
    mime_type = "audio/webm" if is_webm else "audio/wav"

    models_to_try = [s.saaras_model or "saaras:v4", "saaras:v4", "saaras:v3"]
    seen = set()
    models = [m for m in models_to_try if not (m in seen or seen.add(m))]

    last_exc = None
    for model in models:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                data_payload = {
                    "language_code": lang_code,
                    "model": model,
                    "with_timestamps": "false",
                    "with_diacritics": "true",
                    "prompt": prompt_hint or DOMAIN_PROMPT_HINT,
                }
                r = await client.post(
                    f"{s.sarvam_base_url}/speech-to-text",
                    headers={"api-subscription-key": s.sarvam_api_key},
                    files={"file": (filename, audio_bytes, mime_type)},
                    data=data_payload,
                )
                r.raise_for_status()
                body = r.json()
                return {
                    "transcript": body.get("transcript", "").strip(),
                    "confidence": float(body.get("confidence", 0.95)),
                    "timestamps": body.get("timestamps", []),
                    "model_used": model,
                }
        except Exception as exc:
            last_exc = exc
            continue

    if last_exc:
        raise last_exc
    return {"transcript": "", "confidence": 0.0, "timestamps": []}

