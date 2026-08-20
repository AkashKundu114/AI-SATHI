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
async def test_audio_dispatch_downloads_transcribes_and_queues(
    monkeypatch, base_message
):
    processed = []

    async def _download(media_id):
        assert media_id == "audio-media-id"
        return b"audio"

    async def _transcribe(audio_bytes):
        assert audio_bytes == b"audio"
        return {
            "transcript": "আজ ৩০০ টাকা বিক্রি",
            "provider": "fake-stt",
            "confidence": 0.91,
        }

    async def _fake_process_turn(number, turn_input):
        processed.append((number, turn_input))

    monkeypatch.setattr(gateway, "download_whatsapp_audio", _download)
    monkeypatch.setattr(gateway, "transcribe", _transcribe)
    monkeypatch.setattr(gateway, "process_turn_and_dispatch", _fake_process_turn)

    msg = replace_message_audio(base_message)
    await gateway._dispatch_to_orchestrator(msg)

    assert processed == [
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


def replace_message_audio(msg):
    from dataclasses import replace

    return replace(msg, message_type="audio", text=None, audio_id="audio-media-id")


@pytest.mark.asyncio
async def test_image_dispatch_uploads_raw_image_and_queues_catalog_key(
    monkeypatch, base_message
):
    processed = []
    uploads = []

    async def _download(media_id):
        assert media_id == "image-media-id"
        return b"image-bytes"

    def _fake_upload_bytes(key, body, content_type):
        uploads.append({"Key": key, "Body": body, "ContentType": content_type})

    async def _fake_process_turn(number, turn_input):
        processed.append((number, turn_input))

    monkeypatch.setattr(gateway, "download_whatsapp_image", _download)
    monkeypatch.setattr(gateway, "upload_bytes", _fake_upload_bytes)
    monkeypatch.setattr(gateway, "process_turn_and_dispatch", _fake_process_turn)

    from dataclasses import replace

    msg = replace(
        base_message, message_type="image", text=None, image_id="image-media-id"
    )
    await gateway._dispatch_to_orchestrator(msg)

    assert len(uploads) == 1
    assert uploads[0]["Body"] == b"image-bytes"
    assert uploads[0]["ContentType"] == "image/jpeg"
    assert processed[0][0] == "919876543210"
    assert processed[0][1]["last_message_type"] == "image"
    assert processed[0][1]["raw_image_s3_key"].startswith("catalog-raw/919876543210/")
