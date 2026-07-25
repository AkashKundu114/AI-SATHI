from dataclasses import replace

import pytest

from services.gateway import main as gateway
from shared.whatsapp.parser import IncomingMessage


@pytest.fixture
def base_message():
    return IncomingMessage(
        message_id="wamid.TEST",
        from_number="919876543210",
        timestamp=1735689600,
        message_type="text",
        text="হিসাব লিখুন",
    )


@pytest.mark.asyncio
async def test_audio_dispatch_downloads_transcribes_and_queues(monkeypatch, base_message):
    queued = []

    async def _download(media_id):
        assert media_id == "audio-media-id"
        return b"audio"

    async def _transcribe(audio_bytes):
        assert audio_bytes == b"audio"
        return {"transcript": "আজ ৩০০ টাকা বিক্রি", "provider": "fake-stt", "confidence": 0.91}

    class _ProcessTurn:
        @staticmethod
        def delay(number, turn_input):
            queued.append((number, turn_input))

    monkeypatch.setattr(gateway, "download_whatsapp_audio", _download)
    monkeypatch.setattr(gateway, "transcribe", _transcribe)
    monkeypatch.setattr(gateway, "process_turn", _ProcessTurn)

    msg = replace(base_message, message_type="audio", text=None, audio_id="audio-media-id")
    await gateway._dispatch_to_orchestrator(msg)

    assert queued == [
        (
            "919876543210",
            {
                "last_message_type": "audio",
                "raw_input_transcript": "আজ ৩০০ টাকা বিক্রি",
                "transcript_provider": "fake-stt",
                "transcript_confidence": 0.91,
            },
        )
    ]


@pytest.mark.asyncio
async def test_image_dispatch_uploads_raw_image_and_queues_catalog_key(monkeypatch, base_message):
    queued = []
    uploads = []

    async def _download(media_id):
        assert media_id == "image-media-id"
        return b"image-bytes"

    class _S3:
        def put_object(self, **kwargs):
            uploads.append(kwargs)

    class _ProcessTurn:
        @staticmethod
        def delay(number, turn_input):
            queued.append((number, turn_input))

    monkeypatch.setattr(gateway, "download_whatsapp_image", _download)
    monkeypatch.setattr(gateway, "get_s3_client", lambda: _S3())
    monkeypatch.setattr(gateway, "process_turn", _ProcessTurn)

    msg = replace(base_message, message_type="image", text=None, image_id="image-media-id")
    await gateway._dispatch_to_orchestrator(msg)

    assert len(uploads) == 1
    assert uploads[0]["Body"] == b"image-bytes"
    assert uploads[0]["ServerSideEncryption"] == "AES256"
    assert queued[0][0] == "919876543210"
    assert queued[0][1]["last_message_type"] == "image"
    assert queued[0][1]["raw_image_s3_key"].startswith("catalog-raw/919876543210/")
