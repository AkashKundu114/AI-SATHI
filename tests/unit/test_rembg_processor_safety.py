import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import io
from PIL import Image

from services.vision_service.rembg_processor import (
    process_product_image,
    _quality_check,
    MIN_RESOLUTION_PX,
)


def _make_jpeg_bytes(width: int, height: int) -> bytes:
    img = Image.new("RGB", (width, height), color=(200, 150, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_corrupt_bytes_rejected_with_friendly_message():
    result_bytes, error = process_product_image(b"not-an-image-at-all")
    assert result_bytes is None
    assert error is not None


def test_undersized_image_rejected_by_quality_check():
    img = Image.new("RGB", (MIN_RESOLUTION_PX - 10, MIN_RESOLUTION_PX - 10))
    assert _quality_check(img) is not None


def test_oversized_pixel_dimensions_rejected_by_quality_check():
    class _FakeImg:
        width = 20000
        height = 20000
        size = (20000, 20000)

    assert _quality_check(_FakeImg()) is not None


def test_normal_sized_image_passes_quality_check():
    img = Image.new("RGB", (800, 800))
    assert _quality_check(img) is None


def test_truncated_file_rejected_cleanly():
    good_bytes = _make_jpeg_bytes(400, 400)
    truncated = good_bytes[: len(good_bytes) // 2]
    result_bytes, error = process_product_image(truncated)
    assert result_bytes is None
    assert error is not None
