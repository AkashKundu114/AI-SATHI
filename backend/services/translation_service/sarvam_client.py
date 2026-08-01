from __future__ import annotations

import base64
from typing import Any

from shared.config.settings import get_settings

_TIMEOUT = 25.0


class SarvamUnavailableError(Exception):
    pass


def _headers(s) -> dict:
    return {"api-subscription-key": s.sarvam_api_key, "Content-Type": "application/json"}


def _httpx_module() -> Any:
    try:
        import httpx
    except ImportError as exc:

        raise SarvamUnavailableError("httpx package is required") from exc
    return httpx


async def translate(
    text: str,
    target_lang: str = "bn-IN",
    source_lang: str = "auto",
    mode: str = "formal",
    speaker_gender: str = "Male"
) -> str:
    s = get_settings()
    if not s.sarvam_api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY not configured")

    try:
        async with _httpx_module().AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{s.sarvam_base_url}/translate",
                headers=_headers(s),
                json={
                    "input": text,
                    "source_language_code": source_lang,
                    "target_language_code": target_lang,
                    "mode": mode,
                    "speaker_gender": speaker_gender,
                    "model": "mayura:v1",
                },
            )
            r.raise_for_status()
            body = r.json()
        return (body.get("translated_text") or "").strip()
    except Exception as exc:
        raise SarvamUnavailableError(str(exc)) from exc


async def identify_language(text: str) -> str:
    s = get_settings()
    if not s.sarvam_api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY not configured")

    try:
        async with _httpx_module().AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{s.sarvam_base_url}/language-identification",
                headers=_headers(s),
                json={"input": text},
            )
            r.raise_for_status()
            body = r.json()
        return (body.get("language_code") or "bn-IN").strip()
    except Exception:
        return "bn-IN"


async def chat_completion(
    system: str,
    prompt: str,
    model: str | None = None,
    max_tokens: int = 800,
    temperature: float = 0.3
) -> str:
    s = get_settings()
    if not s.sarvam_api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY not configured")

    try:
        async with _httpx_module().AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{s.sarvam_base_url}/v1/chat/completions",
                headers=_headers(s),
                json={
                    "model": model or s.sarvam_chat_model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            r.raise_for_status()
            body = r.json()
        return (body["choices"][0]["message"]["content"] or "").strip()
    except Exception as exc:
        raise SarvamUnavailableError(str(exc)) from exc


async def vision_completion(prompt: str, image_bytes: bytes, max_tokens: int = 700) -> str:
    s = get_settings()
    if not s.sarvam_api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY not configured")

    try:
        async with _httpx_module().AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{s.sarvam_base_url}/vision/completions",
                headers=_headers(s),
                json={
                    "model": s.sarvam_vision_model,
                    "max_tokens": max_tokens,
                    "prompt": prompt,
                    "image": base64.b64encode(image_bytes).decode(),
                },
            )
            r.raise_for_status()
            body = r.json()
        return (body.get("text") or body.get("choices", [{}])[0].get("message", {}).get("content", "") or "").strip()
    except Exception as exc:
        raise SarvamUnavailableError(str(exc)) from exc


async def init_document_intelligence_job(file_bytes: bytes, filename: str = "document.pdf") -> dict:
    s = get_settings()
    if not s.sarvam_api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY not configured")

    try:
        async with _httpx_module().AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{s.sarvam_base_url}/doc-digitization/v1/jobs",
                headers={"api-subscription-key": s.sarvam_api_key},
                files={"file": (filename, file_bytes, "application/pdf")},
                data={"language": "bn-IN"},
            )
            r.raise_for_status()
            return r.json()
    except Exception as exc:
        raise SarvamUnavailableError(str(exc)) from exc


async def chat_completion_self_hosted(system: str, prompt: str, max_tokens: int = 700) -> str:
    s = get_settings()
    if not s.sarvam_local_base_url:
        raise SarvamUnavailableError("SARVAM_LOCAL_BASE_URL not configured")

    try:
        import importlib

        openai_module = importlib.import_module("openai")
        client = openai_module.AsyncOpenAI(base_url=s.sarvam_local_base_url, api_key="not-needed", timeout=30.0, max_retries=0)
        response = await client.chat.completions.create(
            model=s.sarvam_chat_model,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return (response.choices[0].message.content or "").strip()
    except ImportError as exc:
        raise SarvamUnavailableError("openai package is required") from exc
    except Exception as exc:
        raise SarvamUnavailableError(str(exc)) from exc
