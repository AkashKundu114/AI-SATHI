import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


import pytest

from services.orchestrator.nodes import catalog_node as node_module
from services.orchestrator.model_router import ModelUnavailableError


class _FakeS3:
    """Minimal stand-in for boto3's S3 client, covering only the three
    calls catalog_node actually makes."""

    def __init__(self, get_object_bytes=b"fake-image-bytes", raise_on_get=False, raise_on_put=False):
        self._bytes = get_object_bytes
        self.raise_on_get = raise_on_get
        self.raise_on_put = raise_on_put
        self.put_calls = []

    def get_object(self, Bucket, Key):
        if self.raise_on_get:
            raise RuntimeError("s3 get failed")

        data = self._bytes

        class _Body:
            def read(self):
                return data

        return {"Body": _Body()}

    def put_object(self, **kwargs):
        if self.raise_on_put:
            raise RuntimeError("s3 put failed")
        self.put_calls.append(kwargs)

    def generate_presigned_url(self, *args, **kwargs):
        return "https://example.com/presigned-url"


def _default_mocks(monkeypatch, s3=None, process_result=(b"processed", None),
                    vision_info=None, captions=None, prices=(80.0, 250.0), poster=(None, "none")):
    s3 = s3 or _FakeS3()
    monkeypatch.setattr(node_module, "get_s3_client", lambda: s3)

    async def _process(raw_bytes):
        return process_result

    monkeypatch.setattr(node_module, "process_product_image", lambda raw: process_result)

    vision_info = vision_info or {"product_type": "papad", "category": "food", "vision_model_used": "sarvam-vision"}

    async def _analyze(raw_bytes):
        return vision_info

    captions = captions or {"whatsapp_caption": "পাপড় বিক্রির জন্য প্রস্তুত!", "ad_caption": "আজই অর্ডার করুন!"}

    async def _captions(product_info, shg_name=""):
        return captions, prices

    async def _poster(*args, **kwargs):
        return poster

    async def _no_market_note(state, category):
        return None

    monkeypatch.setattr(node_module, "analyze_product_image", _analyze)
    monkeypatch.setattr(node_module, "generate_captions", _captions)
    monkeypatch.setattr(node_module, "generate_poster", _poster)
    monkeypatch.setattr(node_module, "_market_note", _no_market_note)
    return s3


@pytest.mark.asyncio
async def test_missing_image_key_returns_friendly_message():
    result = await node_module.catalog_node({})
    assert result["trace"] == ["catalog_node:no_image_key"]


@pytest.mark.asyncio
async def test_s3_fetch_failure_returns_friendly_message(monkeypatch):
    _default_mocks(monkeypatch, s3=_FakeS3(raise_on_get=True))
    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})
    assert result["trace"] == ["catalog_node:s3_fetch_failed"]


@pytest.mark.asyncio
async def test_oversized_image_rejected_before_processing(monkeypatch):
    oversized = b"x" * (node_module.MAX_IMAGE_BYTES + 1)
    _default_mocks(monkeypatch, s3=_FakeS3(get_object_bytes=oversized))
    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})
    assert result["trace"] == ["catalog_node:oversized_image"]


@pytest.mark.asyncio
async def test_quality_check_failure_returns_the_specific_error_message(monkeypatch):
    _default_mocks(monkeypatch, process_result=(None, "ছবিটা একটু ছোট বা অস্পষ্ট।"))
    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})
    assert result["outbound_messages"][0]["body"] == "ছবিটা একটু ছোট বা অস্পষ্ট।"
    assert result["trace"] == ["catalog_node:quality_check_failed"]


@pytest.mark.asyncio
async def test_vision_model_unavailable_returns_friendly_message(monkeypatch):
    s3 = _FakeS3()
    monkeypatch.setattr(node_module, "get_s3_client", lambda: s3)
    monkeypatch.setattr(node_module, "process_product_image", lambda raw: (b"processed", None))

    async def _raise(raw_bytes):
        raise ModelUnavailableError("sarvam vision down")

    monkeypatch.setattr(node_module, "analyze_product_image", _raise)

    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})
    assert result["trace"] == ["catalog_node:model_unavailable"]


@pytest.mark.asyncio
async def test_processed_image_upload_failure_returns_friendly_message(monkeypatch):
    s3 = _FakeS3(raise_on_put=True)
    _default_mocks(monkeypatch, s3=s3)
    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})
    assert result["trace"] == ["catalog_node:s3_upload_failed"]


@pytest.mark.asyncio
async def test_happy_path_without_poster_falls_back_to_plain_image_and_caption(monkeypatch):
    _default_mocks(monkeypatch, poster=(None, "none"))
    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})

    assert result["catalog_result"]["product_type"] == "papad"
    assert result["catalog_result"]["price_min"] == 80.0
    assert len(result["outbound_messages"]) == 3  # image + ad caption + english-caption offer
    assert result["outbound_messages"][0]["type"] == "image"
    assert "catalog_node:done" in result["trace"][0]
    assert "poster=none" in result["trace"][0]


@pytest.mark.asyncio
async def test_happy_path_with_poster_sends_single_composited_image(monkeypatch):
    _default_mocks(monkeypatch, poster=(b"poster-bytes", "pillow"))
    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})

    assert len(result["outbound_messages"]) == 2  
    assert "poster=pillow" in result["trace"][0]


@pytest.mark.asyncio
async def test_poster_upload_failure_falls_back_to_plain_delivery(monkeypatch):
    s3 = _FakeS3(raise_on_put=False)
    _default_mocks(monkeypatch, s3=s3, poster=(b"poster-bytes", "pillow"))

    def _raise_presigned(*a, **kw):
        raise RuntimeError("presign failed")

    s3.generate_presigned_url = _raise_presigned

    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})
    assert "সমস্যা হচ্ছে" in result["outbound_messages"][0]["body"]
    assert "catalog_node:done:sarvam-vision:poster=none" in result["trace"][0]


@pytest.mark.asyncio
async def test_unknown_vision_category_still_produces_a_result(monkeypatch):
    _default_mocks(monkeypatch, vision_info={"product_type": "kolshi", "category": "other", "vision_model_used": "sarvam-vision"})
    result = await node_module.catalog_node({"raw_image_s3_key": "catalog-raw/x.jpg"})
    assert result["catalog_result"]["product_type"] == "kolshi"


def test_product_label_bengali_uses_local_taxonomy_when_matched():
    assert node_module._product_label_bengali({"product_type": "papad"}) == "পাপড়"


def test_product_label_bengali_falls_back_to_raw_product_type_when_unmatched():
    assert node_module._product_label_bengali({"product_type": "smartphone case"}) == "smartphone case"


def test_product_label_bengali_falls_back_to_generic_label_when_nothing_available():
    assert node_module._product_label_bengali({}) == "পণ্য"


def test_shg_name_reads_from_user_profile():
    assert node_module._shg_name({"user_profile": {"shg_name": "মা দুর্গা গোষ্ঠী"}}) == "মা দুর্গা গোষ্ঠী"


def test_shg_name_defaults_to_empty_string_when_missing():
    assert node_module._shg_name({}) == ""
