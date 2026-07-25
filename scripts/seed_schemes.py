"""Seed scheme_documents / scheme_chunks from official West Bengal
government scheme PDFs placed in data/schemes/raw/.

WHY THIS SCRIPT DELIBERATELY REFUSES TO GUESS ANYTHING:
This product's entire safety story for government schemes (see
docs/architecture.md §5, services/rag_service/grounding_verifier.py) rests
on "only ever answer from content a human actually verified." That
guarantee is worthless if the SEEDING script itself introduces unverified
content -- guessing a scheme's name from a PDF filename, or (worse)
fabricating scheme facts from a web search the way an earlier draft of
this codebase pass considered doing before deciding against it (see
CHANGELOG_v12 at the repo root for that reasoning). So this script:

  1. NEVER writes scheme content the operator didn't supply as a file.
  2. NEVER guesses scheme_name / scheme_code / document_type from a
     filename -- requires an explicit, human-written manifest.json next
     to the PDFs (see MANIFEST_EXAMPLE below). A PDF with no manifest
     entry is skipped and reported, not guessed at.
  3. Chunks and embeds mechanically (no LLM summarization/rewriting of
     the source text at seed time) -- the LLM's only job, at QUERY time,
     is to answer from these exact chunks (services/rag_service/pipeline.py),
     never to have "helped" by paraphrasing at seed time in a way nobody
     can audit against the source PDF afterward.
  4. Prints a clear post-seed summary and reminds the operator this is
     UNAUDITED machine-chunked content -- matches the existing
     scripts/audit_rag.py's human-review-before-trust pattern.

REQUIRES: migrations/0006_scheme_tables.sql applied first (this fixes the
documented "scheme_chunks is altered but never created" bug -- see that
file's own header and DELETE_LIST.md section C). Requires `pypdf` for text
extraction (added to requirements.txt by this pass) and a reachable Ollama
box with `nomic-embed-text` pulled (USE_LOCAL_MODELS=true,
services/rag_service/pipeline.py:get_embedding already expects this).

MANIFEST_EXAMPLE (data/schemes/raw/manifest.json):
{
  "lakshmir_bhandar_guidelines.pdf": {
    "scheme_name": "Lakshmir Bhandar",
    "scheme_code": "LB",
    "document_type": "eligibility",
    "source_url": "https://wb.gov.in/... (put the real official source URL here)"
  }
}
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

RAW_DIR = Path("data/schemes/raw")
MANIFEST_PATH = RAW_DIR / "manifest.json"
CHUNK_CHARS = 800
CHUNK_OVERLAP_CHARS = 100


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        print(
            f"❌ No manifest found at {MANIFEST_PATH}.\n"
            "   This script refuses to guess scheme_name/scheme_code/document_type "
            "from a PDF filename -- write a manifest.json first. See this script's "
            "own MANIFEST_EXAMPLE in the module docstring."
        )
        sys.exit(1)
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def _extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("❌ pypdf not installed. Run: pip install pypdf --break-system-packages")
        sys.exit(1)

    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def _chunk_text(text: str, chunk_chars: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP_CHARS) -> list[str]:
    """Mechanical, non-semantic chunking -- character windows with overlap
    so a fact split across a boundary usually still appears whole in at
    least one chunk. No LLM involved, deliberately -- see module docstring
    point 3. Skips empty/whitespace-only chunks (a scanned PDF with no
    extractable text layer produces these; see the "0 chunks" warning at
    the bottom of this script for what to do about that case)."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
    return chunks


async def _seed_one_pdf(pdf_path: Path, meta: dict) -> dict:
    from services.rag_service.pipeline import get_embedding
    from shared.db.session import get_db_session
    from sqlalchemy import text as sql_text

    full_text = _extract_pdf_text(pdf_path)
    chunks = _chunk_text(full_text)

    if not chunks:
        return {"file": pdf_path.name, "status": "no_extractable_text", "chunks": 0}

    async with get_db_session() as db:
        doc_id_row = (
            await db.execute(
                sql_text(
                    """
                    INSERT INTO scheme_documents
                      (scheme_name, scheme_code, document_type, content_english,
                       source_url, source_file, last_verified_at, is_active)
                    VALUES (:scheme_name, :scheme_code, :document_type, :content_english,
                            :source_url, :source_file, NOW(), TRUE)
                    RETURNING id
                    """
                ),
                {
                    "scheme_name": meta["scheme_name"],
                    "scheme_code": meta.get("scheme_code"),
                    "document_type": meta.get("document_type"),
                    "content_english": full_text[:5000],  # audit reference, not the query-time source of truth
                    "source_url": meta.get("source_url"),
                    "source_file": pdf_path.name,
                },
            )
        ).fetchone()
        document_id = doc_id_row[0]

        for idx, chunk in enumerate(chunks):
            embedding = await get_embedding(chunk)
            emb_str = f"[{','.join(str(x) for x in embedding)}]"
            await db.execute(
                sql_text(
                    """
                    INSERT INTO scheme_chunks (document_id, chunk_text, chunk_bengali, embedding, chunk_index)
                    VALUES (:document_id, :chunk_text, :chunk_bengali, :embedding, :chunk_index)
                    """
                ),
                {
                    "document_id": str(document_id),
                    "chunk_text": chunk,
                    # This script does not translate -- chunk_bengali is left
                    # NULL unless the source PDF itself was already Bengali
                    # (in which case chunk_text IS the Bengali text; a
                    # bilingual PDF needs a smarter per-chunk language split,
                    # which this mechanical version doesn't attempt).
                    "chunk_bengali": chunk if meta.get("source_language") == "bengali" else None,
                    "embedding": emb_str,
                    "chunk_index": idx,
                },
            )
        await db.commit()

    return {"file": pdf_path.name, "status": "seeded", "chunks": len(chunks), "scheme_name": meta["scheme_name"]}


async def main() -> None:
    manifest = _load_manifest()
    pdfs = sorted(RAW_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"No PDFs found in {RAW_DIR}/. Place official scheme PDFs there first (see data/schemes/raw/README.md).")
        return

    results = []
    for pdf_path in pdfs:
        meta = manifest.get(pdf_path.name)
        if not meta:
            print(f"⚠️  Skipping {pdf_path.name} — no manifest entry. Add one to {MANIFEST_PATH} first.")
            results.append({"file": pdf_path.name, "status": "skipped_no_manifest", "chunks": 0})
            continue
        if "scheme_name" not in meta:
            print(f"⚠️  Skipping {pdf_path.name} — manifest entry missing required 'scheme_name'.")
            results.append({"file": pdf_path.name, "status": "skipped_bad_manifest", "chunks": 0})
            continue

        print(f"Processing {pdf_path.name} ({meta['scheme_name']})...")
        try:
            result = await _seed_one_pdf(pdf_path, meta)
        except Exception as exc:
            print(f"❌ Failed on {pdf_path.name}: {exc}")
            result = {"file": pdf_path.name, "status": f"error: {exc}", "chunks": 0}
        results.append(result)

    print("\n" + "=" * 60)
    print("SEEDING SUMMARY (unaudited machine-chunked content — see below)")
    print("=" * 60)
    total_chunks = 0
    for r in results:
        print(f"  {r['file']}: {r['status']} ({r['chunks']} chunks)")
        total_chunks += r["chunks"]
    print(f"\nTotal chunks written: {total_chunks}")
    print(
        "\n⚠️  This content has NOT been human-reviewed for accuracy. Before "
        "trusting this in production, spot-check a sample of chunks against "
        "the source PDFs directly, and run scripts/audit_rag.py once real "
        "query traffic exists — same review discipline the RAG hallucination "
        "audit already expects (docs/product.md Acceptance Criteria, Feature 2)."
    )
    if any(r["status"] == "no_extractable_text" for r in results):
        print(
            "\n⚠️  One or more PDFs produced 0 extractable characters — likely "
            "a scanned image PDF with no text layer. This script does not do "
            "OCR. Re-export the PDF with a text layer, or add an OCR pass "
            "(pdf-reading skill / pytesseract) before re-running."
        )


if __name__ == "__main__":
    asyncio.run(main())
