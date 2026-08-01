from __future__ import annotations

import httpx

from shared.config.settings import get_settings

DOMAIN_PROMPT_HINT = "চাল, আলু, পেঁয়াজ, সরষে, ডাল, দেনা, বিয়োগ, হিসাব, স্বনির্ভর গোষ্ঠী, সিসিএল ঋণ, আনন্দধারা, তাগাদা, ইউপিআই"


async def transcribe(audio_bytes: bytes, language: str = "bn", prompt_hint: str | None = None) -> dict:
    s = get_settings()
    if not s.sarvam_api_key:
        raise RuntimeError("SARVAM_API_KEY not configured")

    lang_code = f"{language}-IN" if len(language) == 2 else language

    async with httpx.AsyncClient(timeout=15.0) as client:
        data_payload = {
            "language_code": lang_code,
            "model": s.saaras_model,
            "with_timestamps": "false",
            "with_diacritics": "true",
            "prompt": prompt_hint or DOMAIN_PROMPT_HINT,
        }
        r = await client.post(
            f"{s.sarvam_base_url}/speech-to-text",
            headers={"api-subscription-key": s.sarvam_api_key},
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            data=data_payload,
        )
        r.raise_for_status()
        body = r.json()

    return {
        "transcript": body.get("transcript", "").strip(),
        "confidence": float(body.get("confidence", 0.95)),
        "timestamps": body.get("timestamps", []),
    }
