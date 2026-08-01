from __future__ import annotations



import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


RAW_DIR = Path("data/schemes/raw")
MANIFEST_PATH = RAW_DIR / "manifest.json"
CHUNK_CHARS = 800
CHUNK_OVERLAP_CHARS = 100

_BENGALI_RANGE = range(0x0980, 0x09FF + 1)
_BENGALI_LANGUAGE_RATIO_THRESHOLD = 0.15


_INSERT_DOCUMENT_SQL = 

_INSERT_CHUNK_SQL = 

_DEACTIVATE_EXISTING_SQL = 

_EXISTING_ACTIVE_SQL = 


def _load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        print(
            f"❌ No manifest found at {MANIFEST_PATH}.\n"
            "   This script refuses to guess scheme_name/scheme_code/document_type "
            "from a PDF filename -- write a manifest.json first. See "
            "data/schemes/raw/README.md for the required shape."
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


def _looks_bengali(text: str) -> bool:
    
    if not text:
        return False
    sample = text[:2000]

    bengali_chars = sum(1 for ch in sample if ord(ch) in _BENGALI_RANGE)
    letter_chars = sum(1 for ch in sample if ch.isalpha() or ord(ch) in _BENGALI_RANGE)
    if letter_chars == 0:
        return False
    return (bengali_chars / letter_chars) >= _BENGALI_LANGUAGE_RATIO_THRESHOLD


async def _seed_one_pdf(pdf_path: Path, meta: dict, *, force: bool, dry_run: bool) -> dict:
    from shared.db.session import get_db_session
    from sqlalchemy import text as sql_text

    full_text = _extract_pdf_text(pdf_path)
    chunks = _chunk_text(full_text)

    if not chunks:
        return {"file": pdf_path.name, "status": "no_extractable_text", "chunks": 0}

    source_language = meta.get("source_language")
    if not source_language:
        source_language = "bengali" if _looks_bengali(full_text) else "english"

    if dry_run:
        return {
            "file": pdf_path.name,
            "status": "dry_run_ok",
            "chunks": len(chunks),
            "scheme_name": meta["scheme_name"],
            "detected_language": source_language,
        }

    from services.rag_service.pipeline import get_embedding

    async with get_db_session() as db:
        existing = (
            await db.execute(sql_text(_EXISTING_ACTIVE_SQL), {"source_file": pdf_path.name})
        ).fetchone()
        if existing and not force:
            return {
                "file": pdf_path.name,
                "status": "skipped_already_seeded (use --force to re-seed)",
                "chunks": 0,
            }
        if existing and force:
            await db.execute(sql_text(_DEACTIVATE_EXISTING_SQL), {"source_file": pdf_path.name})

        doc_id_row = (
            await db.execute(
                sql_text(_INSERT_DOCUMENT_SQL),
                {
                    "scheme_name": meta["scheme_name"],
                    "scheme_code": meta.get("scheme_code"),
                    "document_type": meta.get("document_type"),
                    "content_english": full_text[:5000],

                    "source_url": meta.get("source_url"),
                    "source_file": pdf_path.name,
                },
            )
        ).fetchone()
        document_id = doc_id_row[0]
        await db.commit()

        embedded_count = 0
        failed_chunks: list[int] = []
        for idx, chunk in enumerate(chunks):
            try:
                embedding = await get_embedding(chunk)
                emb_str = f"[{','.join(str(x) for x in embedding)}]"
            except Exception as exc:
                print(f"  ⚠️  chunk {idx} embedding failed, skipping this chunk: {exc}")
                failed_chunks.append(idx)
                continue

            await db.execute(
                sql_text(_INSERT_CHUNK_SQL),
                {
                    "document_id": str(document_id),
                    "chunk_text": chunk,
                    "chunk_bengali": chunk if source_language == "bengali" else None,
                    "embedding": emb_str,
                    "chunk_index": idx,
                },
            )
            embedded_count += 1
        await db.commit()

    status = "seeded" if not failed_chunks else f"seeded_with_{len(failed_chunks)}_chunk_failures"
    return {
        "file": pdf_path.name,
        "status": status,
        "chunks": embedded_count,
        "chunks_failed": len(failed_chunks),
        "scheme_name": meta["scheme_name"],
        "detected_language": source_language,
    }


async def main(args: argparse.Namespace) -> None:
    manifest = _load_manifest()
    pdfs = sorted(RAW_DIR.glob("*.pdf"))

    if args.only:
        pdfs = [p for p in pdfs if p.name == args.only]
        if not pdfs:
            print(f"❌ --only {args.only!r} not found in {RAW_DIR}/")
            sys.exit(1)

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

        print(f"Processing {pdf_path.name} ({meta['scheme_name']})" + (" [dry-run]" if args.dry_run else "") + "...")
        try:
            result = await _seed_one_pdf(pdf_path, meta, force=args.force, dry_run=args.dry_run)
        except Exception as exc:
            print(f"❌ Failed on {pdf_path.name}: {exc}")
            result = {"file": pdf_path.name, "status": f"error: {exc}", "chunks": 0}
        results.append(result)

    print("\n" + "=" * 60)
    print("SEEDING SUMMARY (unaudited machine-chunked content — see below)")
    print("=" * 60)
    total_chunks = 0
    for r in results:
        extra = f" (lang={r['detected_language']})" if "detected_language" in r else ""
        print(f"  {r['file']}: {r['status']} ({r['chunks']} chunks){extra}")
        total_chunks += r["chunks"]
    print(f"\nTotal chunks written: {total_chunks}")

    if not args.dry_run:
        report_path = RAW_DIR / f"seed_report_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        try:
            report_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Report written to {report_path}")
        except OSError as exc:
            print(f"⚠️  Could not write report file: {exc}")

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
    if any(r.get("chunks_failed") for r in results):
        print(
            "\n⚠️  One or more files had chunks that failed to embed (see "
            "warnings above) — those chunks were skipped rather than aborting "
            "the whole file. Re-run with --force after checking the embedding "
            "backend (Ollama reachable? USE_LOCAL_MODELS=true?) if this "
            "matters for completeness."
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                         help="Extract and chunk only — no DB writes, no embedding calls")
    parser.add_argument("--only", type=str, default=None,
                         help="Process a single PDF filename instead of every PDF in data/schemes/raw/")
    parser.add_argument("--force", action="store_true",
                         help="Re-seed a PDF that already has an active scheme_documents row "
                              "(the old row is deactivated, not deleted, preserving the audit trail)")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main(_parse_args()))
