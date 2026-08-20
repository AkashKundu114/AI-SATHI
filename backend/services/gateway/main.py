import asyncio
import hashlib
import hmac
import json
import logging
import os
import sys
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response

from services.gateway.turn_processor import process_turn_and_dispatch
from services.voice_gateway.provider_cascade import transcribe
from shared.config.settings import get_settings
from shared.db.dedup import check_and_increment_rate_limit, mark_seen_or_skip
from shared.security.audit_log import log_security_event
from shared.security.input_sanitizer import sanitize_text_input, validate_phone_number
from shared.storage.blob_client import upload_bytes
from shared.web.media import (
    MediaTooLargeError,
    download_web_audio,
    download_web_image,
)
from shared.web.parser import parse_webhook_payload

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi.staticfiles import StaticFiles

from services.gateway.api_router import router as api_v1_router

logger = logging.getLogger("gateway")

app = FastAPI(title="AI-SATHI Platform API", version="2.0.0", docs_url=None, redoc_url=None)
app.include_router(api_v1_router)


@app.on_event("startup")
async def on_startup():
    try:
        from shared.db.models import Base
        from shared.db.session import get_engine

        engine = get_engine()
        async with engine.begin() as conn:
            from sqlalchemy import text

            try:
                await conn.execute(
                    text(
                        "DO $$ BEGIN "
                        "IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'whatsapp_number') "
                        "AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'phone_number') THEN "
                        "ALTER TABLE users RENAME COLUMN whatsapp_number TO phone_number; "
                        "END IF; END $$;"
                    )
                )
            except Exception as e:
                logger.debug("Column migration check: %s", e)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/initialized.")
    except Exception as exc:
        logger.warning("Startup DB initialization notice: %s", exc)


MAX_WEBHOOK_BODY_BYTES = 1 * 1024 * 1024


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/admin/metrics/email")
async def trigger_metrics_email(request: Request, background_tasks: BackgroundTasks):
    s = get_settings()
    token = request.headers.get("X-Admin-Token", "")
    if not s.admin_api_token or not hmac.compare_digest(token, s.admin_api_token):
        log_security_event(
            "unauthorized_admin_metrics_access", source_ip=request.client.host if request.client else None
        )
        raise HTTPException(status_code=403, detail="Unauthorized")

    recipient = request.query_params.get("to")
    background_tasks.add_task(_collect_and_send_metrics, recipient)
    return {"status": "accepted", "message": "Metrics report email queued"}


async def _collect_and_send_metrics(recipient: str | None = None):
    from shared.observability.email_reporter import send_metrics_email
    from shared.observability.metrics import collect_system_metrics

    metrics = await collect_system_metrics()
    await send_metrics_email(metrics, recipient_email=recipient)


@app.get("/webhook/web")
async def verify_webhook(request: Request):
    s = get_settings()
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == s.wa_webhook_verify_token:
        return Response(content=p.get("hub.challenge", ""), media_type="text/plain")
    log_security_event("webhook_verification_failed", source_ip=request.client.host if request.client else None)
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/web")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    client_ip = request.client.host if request.client else "unknown"
    try:
        s = get_settings()
        body = await request.body()

        if len(body) > MAX_WEBHOOK_BODY_BYTES:
            logger.warning(
                "webhook payload exceeded %d bytes (%d) - dropping before parse",
                MAX_WEBHOOK_BODY_BYTES,
                len(body),
            )
            log_security_event("oversized_webhook_payload", source_ip=client_ip, details={"bytes": len(body)})
            return {"status": "ok"}

        sig = request.headers.get("X-Hub-Signature-256", "")

        expected = "sha256=" + hmac.new(s.wa_app_secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            logger.warning("webhook signature mismatch - dropping payload")
            log_security_event("hmac_signature_mismatch", source_ip=client_ip)
            raise HTTPException(status_code=403)

        payload = json.loads(body)
        msg = parse_webhook_payload(payload)
        if not msg:
            return {"status": "ok"}

        if not validate_phone_number(msg.from_number):
            logger.warning("invalid phone number format: %s - dropping", msg.from_number)
            log_security_event("invalid_phone_number", source_ip=client_ip, details={"phone": msg.from_number})
            return {"status": "ok"}

        if msg.text:
            msg.text = sanitize_text_input(msg.text, max_chars=s.max_text_message_chars or 2000)

        is_new = await mark_seen_or_skip(msg.message_id)
        if not is_new:
            return {"status": "ok"}

        under_limit = await check_and_increment_rate_limit(msg.from_number, s.max_messages_per_hour)
        if not under_limit:
            log_security_event("rate_limit_exceeded", source_ip=client_ip, phone_number=msg.from_number)
            return {"status": "ok"}

        background_tasks.add_task(_dispatch_to_orchestrator, msg)
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception:
        logger.exception("receive_message: unhandled error, swallowing to protect webhook")
        return {"status": "ok"}


async def _dispatch_to_orchestrator(msg):
    turn_input: dict = {"last_message_type": msg.message_type}

    try:
        if msg.message_type == "text":
            turn_input["raw_input_text"] = msg.text

        elif msg.message_type == "audio":
            if getattr(msg, "audio_id", None):
                audio_bytes = await download_web_audio(msg.audio_id)
            else:
                audio_bytes = getattr(msg, "audio_bytes", None) or b""
            stt_result = await transcribe(audio_bytes)
            turn_input["raw_input_transcript"] = stt_result["transcript"]
            turn_input["transcript_provider"] = stt_result["provider"]
            turn_input["transcript_confidence"] = stt_result["confidence"]

        elif msg.message_type == "image":
            if getattr(msg, "image_id", None):
                image_bytes = await download_web_image(msg.image_id)
            else:
                image_bytes = getattr(msg, "image_bytes", None) or b""
            key = f"catalog-raw/{msg.from_number}/{uuid.uuid4().hex[:10]}.jpg"
            upload_bytes(key, image_bytes, content_type="image/jpeg")
            turn_input["raw_image_s3_key"] = key

        elif msg.message_type == "interactive":
            turn_input["raw_input_text"] = json.dumps(msg.interactive_payload or {})

        else:
            return

        await process_turn_and_dispatch(msg.from_number, turn_input)

    except MediaTooLargeError:
        from shared.web.sender import send_text

        friendly = (
            "ভয়েস নোটটা অনেক বড়। ৩ মিনিটের কম রেকর্ড করে আবার পাঠান।"
            if msg.message_type == "audio"
            else "ছবিটা অনেক বড়। একটু ছোট সাইজে পাঠান।"
        )
        await send_text(msg.from_number, friendly)

    except Exception:
        logger.exception("_dispatch_to_orchestrator: unhandled error for %s", msg.from_number)
        from shared.web.sender import send_text

        await send_text(msg.from_number, "দুঃখিত, একটু সমস্যা হয়েছে। আবার চেষ্টা করুন।")


candidate_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dist"),
    "/app/frontend/dist",
    "/app/dist",
    os.path.join(os.getcwd(), "frontend", "dist"),
]
web_dist_path = next((p for p in candidate_paths if os.path.isdir(p)), None)
if web_dist_path:
    logger.info("Serving web UI static assets from %s", web_dist_path)
    app.mount("/", StaticFiles(directory=web_dist_path, html=True), name="static")

