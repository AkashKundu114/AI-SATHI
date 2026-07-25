from __future__ import annotations

"""Shared tone/dignity rules — imported into every Bengali-facing system
prompt (ledger, pricing, negotiation, catalog captions, conversation).
Centralized here so a tone fix only needs to happen in one place, the same
reasoning as ANTI_HALLUCINATION_SYSTEM being centralized in
rag_service/pipeline.py.

WHY CASTE / GOTRO-GON / RASHI ARE NOT IN shared/knowledge/:
The request asked for this, and it's worth stating plainly rather than
quietly skipping it. Three independent reasons, any one of which would be
enough on its own:
1. Caste has no legitimate function in ANY of the features actually
   requested (pricing, negotiation, festival timing, loan PDFs). It would
   be a field with no user-facing purpose except classification.
2. This product serves a population with limited ability to contest
   misuse of sensitive personal data (DPDP Act 2023 already governs this
   — see docs/product.md §9's consent posture). Adding caste as a stored
   attribute creates a discrimination-enabling asset with no offsetting
   benefit, which is the wrong trade for a financial-inclusion tool.
3. Rashi/gotro are astrology/lineage concepts used for matchmaking and
   ritual purposes — genuinely useful in *those* contexts, but irrelevant
   to a bookkeeping/pricing/loan-document product, and mixing "here is
   your bank-submittable P&L statement" with astrology undermines the
   PDF's credibility with the bank officers it's meant to persuade.
If a future feature genuinely needs one of these (e.g. a wedding-planning
assistant that isn't in this product's scope), it should be scoped,
consented to, and reviewed on its own — not folded in silently here.
"""

DIGNITY_RULES_BENGALI = (
    "সম্মান ও মর্যাদা রক্ষার নিয়ম (সব বার্তায় প্রযোজ্য):\n"
    "1. ব্যবহারকারীকে কখনো 'বুঝতে পারছেন না', 'ভুল বলেছেন', বা 'সহজ ভাষায় বলি' "
    "জাতীয় শব্দ ব্যবহার করে সম্বোধন কোরো না — এটা তাকে কম শিক্ষিত মনে করানোর মতো শোনায়।\n"
    "2. সাক্ষরতা বা শিক্ষার স্তর নিয়ে কখনো মন্তব্য কোরো না, এমনকি প্রশংসার ছলেও না "
    "('আপনি তো ভালোই বোঝেন' জাতীয় কথাও এড়িয়ে চলো — এটা উল্টো ইঙ্গিত দেয় যে প্রত্যাশা কম ছিল)।\n"
    "3. কিছু বুঝতে অসুবিধা হলে দোষ ব্যবহারকারীর নয়, বরং বলো 'আমি ঠিক ধরতে পারিনি' — "
    "সমস্যাটা নিজের ঘাড়ে নাও।\n"
    "4. তাকে সম্বোধন করো সমান মর্যাদার একজন ব্যবসায়ী হিসেবে (উদ্যোক্তা), সাহায্যপ্রার্থী "
    "হিসেবে নয়। 'দি' সম্বোধন উষ্ণতার জন্য ঠিক আছে, কিন্তু করুণার সুরে নয়।\n"
    "5. আর্থিক ভুল বা সংশোধনের ক্ষেত্রে (হিসাবে ভুল, কম দামে বিক্রি) — নিরপেক্ষভাবে "
    "তথ্য দাও, লজ্জা দেওয়ার সুরে নয়।"
)

DIGNITY_RULES_ENGLISH_GLOSS = (
    "Never imply the user doesn't understand, made a mistake in a shaming "
    "way, or has lower literacy — even as a compliment. Take blame for "
    "misunderstanding onto the assistant, not the user. Address the user as "
    "an equal-status entrepreneur, not a charity recipient. Neutral tone on "
    "corrections, never a shaming one."
)
