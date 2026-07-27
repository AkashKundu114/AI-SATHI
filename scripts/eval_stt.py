from __future__ import annotations

"""
STT eval script — loads an eval-set JSONL, runs it through a configured
STT provider, and reports Word Error Rate (WER) against reference
transcripts.

This was previously a stub (`print("STT eval script — ...")`). This is a
real implementation. No new dependency was added: WER is computed with a
self-contained word-level Levenshtein-distance implementation
(`_word_error_rate`) rather than pulling in `jiwer` or similar, since
requirements.txt doesn't currently include one.

Eval-set format (JSONL, one object per line):
    {"audio_path": "eval/samples/001.wav", "reference": "আজ তিনশো টাকা পাপড় বিক্রি করেছি"}

Usage:
    python3 scripts/eval_stt.py --eval-set data/stt_eval/eval.jsonl
    python3 scripts/eval_stt.py --eval-set data/stt_eval/eval.jsonl --provider whisper-local --limit 20
    python3 scripts/eval_stt.py --eval-set data/stt_eval/eval.jsonl --output results.csv

Provider choices:
    whisper-local  self-hosted faster-whisper (default — needs no API key)
    saaras         Sarvam's Saaras V3 (needs SARVAM_API_KEY set)
    cascade        the production provider_cascade.transcribe() (Saaras -> whisper-local)
"""

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _word_error_rate(reference: str, hypothesis: str) -> dict:
    """Word-level Levenshtein distance (substitutions + insertions +
    deletions), normalized by reference word count — the standard WER
    definition used in docs/product.md's G6 target (WER <= 0.08)."""
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    r, h = len(ref_words), len(hyp_words)

    dp = [[0] * (h + 1) for _ in range(r + 1)]
    for i in range(r + 1):
        dp[i][0] = i
    for j in range(h + 1):
        dp[0][j] = j
    for i in range(1, r + 1):
        for j in range(1, h + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    distance = dp[r][h]
    wer = (distance / r) if r > 0 else (0.0 if h == 0 else 1.0)
    return {"wer": wer, "edit_distance": distance, "ref_words": r, "hyp_words": h}


def _load_eval_set(path: Path, limit: int | None) -> list[dict]:
    samples = []
    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                print(f"⚠️  Skipping malformed JSON on line {line_no} of {path}")
                continue
            if "audio_path" not in obj or "reference" not in obj:
                print(f"⚠️  Skipping line {line_no} — missing 'audio_path' or 'reference' field")
                continue
            samples.append(obj)
            if limit and len(samples) >= limit:
                break
    return samples


async def _transcribe_with_provider(provider: str, audio_bytes: bytes) -> dict:
    if provider == "whisper-local":
        from services.voice_gateway.providers import whisper_local_provider
        return await whisper_local_provider.transcribe(audio_bytes)
    if provider == "saaras":
        from services.voice_gateway.providers import saaras_provider
        return await saaras_provider.transcribe(audio_bytes)
    if provider == "cascade":
        from services.voice_gateway.provider_cascade import transcribe
        return await transcribe(audio_bytes)
    raise ValueError(f"unknown provider: {provider!r}")


async def main_async(eval_set: Path, provider: str, limit: int | None, output: Path) -> None:
    if not eval_set.exists():
        print(f"❌ Eval set not found at {eval_set}")
        return

    samples = _load_eval_set(eval_set, limit)
    if not samples:
        print("No valid samples found in eval set.")
        return

    print(f"Loaded {len(samples)} sample(s). Running provider={provider!r}...")

    rows = []
    total_edit_distance = 0
    total_ref_words = 0
    failures = 0

    for i, sample in enumerate(samples, start=1):
        audio_path = Path(sample["audio_path"])
        reference = sample["reference"]

        if not audio_path.exists():
            print(f"[{i}/{len(samples)}] ⚠️  missing audio file: {audio_path}")
            failures += 1
            continue

        audio_bytes = audio_path.read_bytes()
        try:
            stt_result = await _transcribe_with_provider(provider, audio_bytes)
        except Exception as exc:
            print(f"[{i}/{len(samples)}] ❌ transcription failed for {audio_path}: {exc}")
            failures += 1
            continue

        hypothesis = stt_result.get("transcript", "")
        metrics = _word_error_rate(reference, hypothesis)
        rows.append({
            "audio_path": str(audio_path),
            "reference": reference,
            "hypothesis": hypothesis,
            "wer": round(metrics["wer"], 4),
            "edit_distance": metrics["edit_distance"],
            "ref_words": metrics["ref_words"],
            "confidence": stt_result.get("confidence"),
            "provider_used": stt_result.get("provider", provider),
        })
        total_edit_distance += metrics["edit_distance"]
        total_ref_words += metrics["ref_words"]
        print(f"[{i}/{len(samples)}] WER={metrics['wer']:.3f}  ref={reference[:40]!r}  hyp={hypothesis[:40]!r}")

    if rows:
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "audio_path", "reference", "hypothesis", "wer", "edit_distance",
                "ref_words", "confidence", "provider_used",
            ])
            writer.writeheader()
            writer.writerows(rows)

    overall_wer = (total_edit_distance / total_ref_words) if total_ref_words else float("nan")
    print("\n" + "=" * 60)
    print(f"Samples evaluated: {len(rows)}  |  Failed/skipped: {failures}")
    print(f"Overall WER (edit-distance-weighted across all samples): {overall_wer:.4f}")
    print("PRD target (docs/product.md §4.2 G6): WER <= 0.08 (>=92% accuracy)")
    if rows:
        print(f"Results written to {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eval-set", type=Path, required=True, help="Path to eval-set JSONL")
    parser.add_argument(
        "--provider", choices=["whisper-local", "saaras", "cascade"], default="whisper-local",
        help="Which STT provider to evaluate (default: whisper-local, needs no API key)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N samples")
    parser.add_argument("--output", type=Path, default=Path("stt_eval_results.csv"), help="CSV output path")
    args = parser.parse_args()

    asyncio.run(main_async(args.eval_set, args.provider, args.limit, args.output))


if __name__ == "__main__":
    main()
