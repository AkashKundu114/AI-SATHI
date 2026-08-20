from __future__ import annotations

import logging
import re
from typing import Any

from services.orchestrator.model_router import ModelUnavailableError, TaskCriticality, route_completion
from shared.guardrails.output_guard import enforce_output_guard

logger = logging.getLogger("pdf_rag_engine")

_sample_documents_kb: dict[str, str] = {
    "anandadhara_loan_guidelines.pdf": (
        "পশ্চিমবঙ্গ আনন্দধারা প্রকল্প স্বনির্ভর গোষ্ঠী (SHG) ঋণ নির্দেশিকা ২০২৬:\n"
        "১. স্বনির্ভর গোষ্ঠীর সর্বনিম্ন সদস্য সংখ্যা ১০ জন হতে হবে।\n"
        "২. ৬ মাস সফলভাবে পঞ্চসূত্র পালনের পর প্রথম কিস্তির সিসিএল (CCL) ঋণ সর্বোচ্চ ২ লক্ষ টাকা পাওয়া যাবে।\n"
        "৩. দ্বিতীয় বছরে ঋণের পরিমাণ বাড়িয়ে ৫ লক্ষ টাকা করা যাবে। সুদের হার বছরে ৭% (সময়মতো পরিশোধ করলে ৪% সুদে ভাজ ছাড় পাওয়া যাবে)।\n"
        "৪. প্রয়োজনীয় নথি: দলের রেজোলিউশন খাতা, আধার কার্ড, ব্যাংক পাসবইয়ের জেরক্স ও পাসপোর্ট সাইজ ছবি।"
    ),
    "wb_agriculture_subsidy.pdf": (
        "পশ্চিমবঙ্গ কৃষি দপ্তর অনুদান ও বীজ সহায়তা স্কিম ২০২৬:\n"
        "১. ক্ষুদ্র ও প্রান্তিক কৃষকদের জন্য উন্নতমানের আলু ও সরষে বীজে ৫০% ভুর্তুকি প্রদান করা হচ্ছে।\n"
        "২. সোলার পাম্প সেট বসানোর জন্য রাজ্য সরকার ৭৫% পর্যন্ত অনুদান দিচ্ছে।\n"
        "৩. বাংলা শস্য বীমা (BSB) স্কিমে প্রাকৃতিক দুর্যোগে ফসল ক্ষতির সম্পূর্ণ প্রিমিয়াম রাজ্য সরকার বহন করবে।"
    ),
}


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks or [text]


async def query_pdf_rag(doc_name: str, doc_text: str, question: str) -> dict[str, Any]:
    context = doc_text or _sample_documents_kb.get(doc_name, "")
    if not context:
        return {
            "answer": "দুঃখিত, এই ডকুমেন্টটির টেক্সট পাওয়া যায়নি। অন্য একটি PDF ফাইল আপলোড করুন।",
            "sources": [],
            "doc_name": doc_name,
        }

    chunks = chunk_text(context)
    keywords = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 2]

    scored_chunks = []
    for c in chunks:
        score = sum(1 for kw in keywords if kw in c.lower())
        scored_chunks.append((score, c))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_context = "\n---\n".join(c[1] for c in scored_chunks[:3])

    system_prompt = (
        "তুমি একজন বিশ্বস্ত সরকারি ও আইনি ডকুমেন্ট সহায়ক। দেওয়া ডকুমেন্টের তথ্যের ওপর ভিত্তি করে প্রশ্নের সঠিক সংক্ষেপিত উত্তর দাও।\n"
        "নিয়ম:\n"
        "১. শুধুমাত্র দেওয়া তথ্যের ভিত্তিতে বাংলা ভাষায় ৩-৪ লাইনে স্পষ্ট উত্তর দাও।\n"
        "২. মনগড়া কোনো নিয়ম বা সংখ্যা যোগ করবে না।"
    )
    prompt = f"ডকুমেন্ট সারসংক্ষেপ:\n{top_context}\n\nব্যবহারকারীর প্রশ্ন: {question}"

    try:
        res = await route_completion(
            system=system_prompt, prompt=prompt, criticality=TaskCriticality.ROUTINE, confidence_floor=0.0
        )
        answer = enforce_output_guard(res["text"], fallback="ডকুমেন্ট থেকে উত্তর পাওয়া যায়নি।")
    except ModelUnavailableError:
        answer = f"ডকুমেন্ট সারসংক্ষেপের ভিত্তিতে:\n{top_context[:300]}…"

    return {
        "answer": answer,
        "sources": [top_context[:150] + "…"],
        "doc_name": doc_name,
    }
