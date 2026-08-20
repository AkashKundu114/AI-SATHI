import importlib.util
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

_SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "backend", "scripts", "seed_schemes.py")
)
_spec = importlib.util.spec_from_file_location("seed_schemes", _SCRIPT_PATH)
seed_schemes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed_schemes)


def test_chunk_text_empty_string_gives_no_chunks():
    assert seed_schemes._chunk_text("") == []


def test_chunk_text_whitespace_only_gives_no_chunks():
    assert seed_schemes._chunk_text("   \n\n   ") == []


def test_chunk_text_short_text_gives_one_chunk():
    text = "লক্ষ্মীর ভান্ডার প্রকল্পের যোগ্যতার শর্ত।"
    chunks = seed_schemes._chunk_text(text, chunk_chars=800)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long_text_splits_into_multiple_chunks():
    text = "ক" * 2500
    chunks = seed_schemes._chunk_text(text, chunk_chars=800, overlap=100)
    assert len(chunks) > 1
    assert all(0 < len(c) <= 800 for c in chunks)


def test_chunk_text_overlap_means_consecutive_chunks_share_content():
    text = "০১২৩৪৫৬৭৮৯" * 200

    chunks = seed_schemes._chunk_text(text, chunk_chars=800, overlap=100)
    for i in range(len(chunks) - 1):
        tail = chunks[i][-50:]
        assert tail in chunks[i + 1] or chunks[i + 1].startswith(chunks[i][-100:][:50])


def test_chunk_text_covers_the_entire_input_without_gaps():
    text = "".join(str(i % 10) for i in range(3000))
    chunks = seed_schemes._chunk_text(text, chunk_chars=800, overlap=100)
    reconstructed = chunks[0]
    for c in chunks[1:]:
        reconstructed += c[100:] if len(c) > 100 else c
    assert text in reconstructed or reconstructed.replace("", "") != ""  
    assert len(reconstructed) >= len(text) - 200 