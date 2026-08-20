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
    mode: str = "modern-colloquial",
    numerals_format: str = "international",
    speaker_gender: str = "Male",
) -> str:
    s = get_settings()
    if not s.sarvam_api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY not configured")

    try:
        try:
            from sarvamai import SarvamAI

            client = SarvamAI(api_subscription_key=s.sarvam_api_key)
            src_lang = "bn-IN" if source_lang == "auto" else source_lang
            res = client.text.translate(
                input=text,
                source_language_code=src_lang,
                target_language_code=target_lang,
                model="mayura:v1",
                numerals_format=numerals_format,
                mode=mode,
            )
            if hasattr(res, "translated_text") and res.translated_text:
                return res.translated_text.strip()
        except ImportError:
            pass

        async with _httpx_module().AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                f"{s.sarvam_base_url}/translate",
                headers=_headers(s),
                json={
                    "input": text,
                    "source_language_code": source_lang,
                    "target_language_code": target_lang,
                    "mode": mode,
                    "numerals_format": numerals_format,
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
    system: str, prompt: str, model: str | None = None, max_tokens: int = 1024, temperature: float = 0.3
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


async def digitize_document(
    file_bytes: bytes, filename: str = "document.pdf", language: str = "bn-IN", output_format: str = "md"
) -> dict:
    """
    Digitizes a document (bills, invoices, passbooks) using Sarvam Parse Document Intelligence.
    Supports both official sarvamai SDK and REST API with polling.
    """
    s = get_settings()
    if not s.sarvam_api_key:
        raise SarvamUnavailableError("SARVAM_API_KEY not configured")

    try:
        import os
        import tempfile

        from sarvamai import SarvamAI

        client = SarvamAI(api_subscription_key=s.sarvam_api_key)
        job = client.document_intelligence.create_job(
            language=language, output_format="html" if output_format == "html" else "markdown"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            job.upload_file(tmp_path)
            job.start()
            status = job.wait_until_complete()
            metrics = job.get_page_metrics()
            return {"job_id": job.job_id, "status": getattr(status, "job_state", "completed"), "metrics": metrics}
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception:
        pass

    try:
        import asyncio

        async with _httpx_module().AsyncClient(timeout=60.0) as client:
            submit = await client.post(
                "https://api.sarvam.ai/doc-ai/v1/job/digitise",
                headers={"api-subscription-key": s.sarvam_api_key},
                files={"file": (filename, file_bytes, "application/pdf")},
                data={
                    "language": language,
                    "output_format": output_format,
                    "content_type": "mixed",
                    "auto_orient": "true",
                },
            )
            submit.raise_for_status()
            job_data = submit.json()
            job_id = job_data.get("job_id")

            if job_id:
                for _ in range(30):
                    await asyncio.sleep(2)
                    status_res = await client.get(
                        f"https://api.sarvam.ai/doc-ai/v1/job/{job_id}/status",
                        headers={"api-subscription-key": s.sarvam_api_key},
                    )
                    if status_res.status_code == 200:
                        status_data = status_res.json()
                        if status_data.get("status") in ["completed", "partially_completed"]:
                            return status_data
                        if status_data.get("status") in ["failed", "rejected"]:
                            break
            return job_data
    except Exception as exc:
        raise SarvamUnavailableError(str(exc)) from exc


async def chat_completion_self_hosted(system: str, prompt: str, max_tokens: int = 700) -> str:
    s = get_settings()
    if not s.sarvam_local_base_url:
        raise SarvamUnavailableError("SARVAM_LOCAL_BASE_URL not configured")

    try:
        import importlib

        openai_module = importlib.import_module("openai")
        client = openai_module.AsyncOpenAI(
            base_url=s.sarvam_local_base_url, api_key="not-needed", timeout=30.0, max_retries=0
        )
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
