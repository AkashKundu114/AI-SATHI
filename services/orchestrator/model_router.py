from __future__ import annotations

import base64
import importlib
import json
import logging
import time
from enum import Enum

try:
    httpx = importlib.import_module("httpx")
except ImportError:  
    httpx = None 

from shared.config.settings import get_settings
from services.translation_service import sarvam_client
from services.translation_service.sarvam_client import SarvamUnavailableError

logger = logging.getLogger("model_router")


class TaskCriticality(str, Enum):
    SAFETY_CRITICAL = "safety_critical" 
    ROUTINE = "routine"


class AgentTier(str, Enum):

    STANDARD = "standard"   
    ADVANCED = "advanced"   


class ModelUnavailableError(Exception):
    pass


_BREAKER_FAILURE_THRESHOLD = 5
_BREAKER_COOLDOWN_SECONDS = 30.0

_breaker_state = {"consecutive_failures": 0, "open_until": 0.0}


def _breaker_is_open() -> bool:
    return time.monotonic() < _breaker_state["open_until"]


def _record_sarvam_failure() -> None:
    _breaker_state["consecutive_failures"] += 1
    if _breaker_state["consecutive_failures"] >= _BREAKER_FAILURE_THRESHOLD:
        _breaker_state["open_until"] = time.monotonic() + _BREAKER_COOLDOWN_SECONDS
        logger.warning(
            "Sarvam circuit breaker opened after %d consecutive failures — "
            "skipping Sarvam for %.0fs",
            _breaker_state["consecutive_failures"], _BREAKER_COOLDOWN_SECONDS,
        )


def _record_sarvam_success() -> None:
    _breaker_state["consecutive_failures"] = 0
    _breaker_state["open_until"] = 0.0


def _reset_breaker_for_tests() -> None:
    _breaker_state["consecutive_failures"] = 0
    _breaker_state["open_until"] = 0.0


def _parse_self_reported_confidence(text: str) -> float:
    try:
        parsed = json.loads(text)
        return float(parsed.get("confidence", parsed.get("overall_confidence", 0.0)))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0.0


async def _call_local_ollama(system: str, prompt: str) -> tuple[str, float]:
    if httpx is None:
        raise ModelUnavailableError("local Ollama unavailable because httpx is not installed")

    s = get_settings()
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{s.ollama_base_url}/api/generate",
            json={
                "model": s.ollama_llm_model,
                "system": system,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 512},
            },
        )
        r.raise_for_status()
        text = r.json()["response"].strip()
    return text, _parse_self_reported_confidence(text)


async def route_completion(
    *,
    system: str,
    prompt: str,
    criticality: TaskCriticality,
    tier: AgentTier = AgentTier.STANDARD,
    confidence_floor: float = 0.80,
) -> dict:
    s = get_settings()
    model_name = s.sarvam_advanced_model if tier == AgentTier.ADVANCED else s.sarvam_chat_model

    if s.sarvam_api_key and not _breaker_is_open():
        try:
            text = await sarvam_client.chat_completion(system, prompt, model=model_name)
            _record_sarvam_success()
            if _parse_self_reported_confidence(text) >= confidence_floor:
                return {"text": text, "model_used": f"sarvam-{tier.value}", "escalated": False}
            logger.warning("Sarvam (%s) low self-reported confidence, falling through to local", tier.value)
        except SarvamUnavailableError as exc:
            _record_sarvam_failure()
            logger.warning("Sarvam (%s) unavailable, falling through to local: %s", tier.value, exc)
    elif s.sarvam_api_key and _breaker_is_open():
        logger.info("Sarvam circuit breaker open — skipping Sarvam call, going straight to local fallback")

    if s.use_local_models:
        try:
            text, local_confidence = await _call_local_ollama(system, prompt)
            if local_confidence >= confidence_floor:
                return {"text": text, "model_used": "ollama-local", "escalated": True}
            logger.warning("local Ollama low self-reported confidence (%.2f)", local_confidence)
            return {"text": text, "model_used": "ollama-local", "escalated": True}
        except Exception as exc:
            logger.error("local Ollama unavailable: %s", exc)
            raise ModelUnavailableError(str(exc)) from exc

    raise ModelUnavailableError(
        "Sarvam unavailable/unconfigured and USE_LOCAL_MODELS is false — no fallback tier configured"
    )


async def route_translation(text: str, target_lang: str, source_lang: str = "auto") -> dict:
    s = get_settings()

    if s.sarvam_api_key:
        try:
            translated = await sarvam_client.translate(text, target_lang=target_lang, source_lang=source_lang)
            if translated:
                return {"text": translated, "model_used": "sarvam-translate"}
        except SarvamUnavailableError as exc:
            logger.warning("Sarvam translate unavailable, falling through: %s", exc)

    if s.sarvam_local_base_url:
        try:
            translated = await sarvam_client.chat_completion_self_hosted(
                system=f"Translate the user's message to {target_lang}. Reply with only the translation, nothing else.",
                prompt=text,
                max_tokens=300,
            )
            if translated:
                return {"text": translated, "model_used": "sarvam-local"}
        except SarvamUnavailableError as exc:
            logger.warning("self-hosted translation box unavailable, falling through: %s", exc)

    if s.use_local_models:
        try:
            text_out, _ = await _call_local_ollama(
                system=f"Translate the user's message to {target_lang}. Reply with only the translation, nothing else.",
                prompt=text,
            )
            if text_out:
                return {"text": text_out, "model_used": "ollama-local"}
        except Exception as exc:
            logger.error("local Ollama translation failed: %s", exc)

    raise ModelUnavailableError("no translation tier available (Sarvam and local Ollama both failed/unconfigured)")


async def _call_local_vision(prompt: str, image_bytes: bytes) -> tuple[str, bool]:
    if httpx is None:
        return "", False

    s = get_settings()
    image_b64 = base64.b64encode(image_bytes).decode()
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            r = await client.post(
                f"{s.ollama_base_url}/api/generate",
                json={"model": s.ollama_vision_model, "prompt": prompt, "images": [image_b64], "stream": False},
            )
            r.raise_for_status()
            text = r.json().get("response", "").strip()
            return text, bool(text)
    except (httpx.HTTPError, KeyError, ValueError):
        return "", False


async def route_vision_completion(*, prompt: str, image_bytes: bytes, criticality: TaskCriticality) -> dict:
    s = get_settings()

    if s.sarvam_api_key:
        try:
            text = await sarvam_client.vision_completion(prompt, image_bytes)
            if text:
                return {"text": text, "model_used": "sarvam-vision", "escalated": False}
        except SarvamUnavailableError as exc:
            logger.warning("Sarvam Vision unavailable, falling through to local: %s", exc)

    if s.use_local_models:
        text, ok = await _call_local_vision(prompt, image_bytes)
        if ok:
            return {"text": text, "model_used": "ollama-vision", "escalated": True}

    raise ModelUnavailableError(
        "no vision tier available (Sarvam Vision failed/unconfigured, local vision not enabled)"
    )
