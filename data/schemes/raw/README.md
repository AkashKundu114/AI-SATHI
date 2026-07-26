# Government Scheme PDFs

Place official West Bengal government scheme PDFs here, then run:
```bash
python3 scripts/seed_schemes.py
```

**As of this pass, `seed_schemes.py` is a real implementation, not a
stub** — it extracts text (`pypdf`), chunks it mechanically, embeds each
chunk via your local Ollama `nomic-embed-text` (requires
`USE_LOCAL_MODELS=true` and that model pulled — see `SETUP.md`), and
writes to `scheme_documents`/`scheme_chunks` (schema fixed by
`migrations/0006_scheme_tables.sql` — see that file's header for why a fix
was needed).

## Required: `manifest.json`

The script refuses to guess which scheme a PDF belongs to from its
filename — you must create `manifest.json` in this same directory:

```json
{
  "lakshmir_bhandar_guidelines.pdf": {
    "scheme_name": "Lakshmir Bhandar",
    "scheme_code": "LB",
    "document_type": "eligibility",
    "source_url": "https://<the real official wb.gov.in / anandadhara.wb.gov.in URL>"
  }
}
```

A PDF with no manifest entry is skipped and reported, not guessed at —
this matters because everything this system tells a user about scheme
eligibility ultimately traces back to what's in this table (see
`docs/architecture.md` §5 and `services/rag_service/grounding_verifier.py`).

## Why no scheme content ships pre-filled in this repo

An earlier pass of this codebase's development considered pulling current
Lakshmir Bhandar / Kanyashree / etc. figures from a web search and seeding
them directly. That was deliberately **not done** — the search results for
even a single well-known scheme (Lakshmir Bhandar) turned up genuinely
conflicting monthly amounts across sources (₹1000–1200 vs ₹1500–1700 vs a
claimed ₹3000 replacement scheme tied to a contested post-election
government transition), several from non-official SEO aggregator sites
rather than the government portal itself. Writing an uncertain number into
a table this product treats as ground truth for a "zero hallucinated
scheme amounts" product would have directly undermined the one guarantee
this feature exists to make. Feed this from real official PDFs you've
personally verified, not from anyone's web search — including this one.

## Schemes to include at launch (per docs/product.md §5, Feature 2)

- [ ] Lakshmir Bhandar guidelines
- [ ] Anandadhara scheme document
- [ ] SVSKP scheme guidelines
- [ ] Krishak Bandhu guidelines
- [ ] WBSSP scheme document
- [ ] JAAGO scheme guidelines
- [ ] Kanyashree guidelines
- [ ] Rupashree guidelines

Sources: wb.gov.in, anandadhara.wb.gov.in, wbfin.nic.in — the official
government portals specifically, not third-party aggregator sites.

## Note on scheme availability changing

Several West Bengal welfare schemes have seen genuine administrative
changes recently (renamed, replaced, or restructured programs tied to
state-level political transitions) — verify a scheme is still the current,
active program before ingesting its PDF, not just that the PDF exists.
This is exactly the kind of fast-moving administrative fact `docs/product.md`
already asks the (currently unrouted) weekly-refresh scraper to catch —
see `docs/product.md` FR2.6.
