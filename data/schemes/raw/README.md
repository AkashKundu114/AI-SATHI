# Government Scheme Source PDFs

Government Scheme RAG is present in the repository, but it is not part of the
active production route. Treat this directory as source-data staging for a
future re-enable, not as required setup for the current deployment.

## Seeding

Place official West Bengal government scheme PDFs here, then run:

```bash
python3 scripts/seed_schemes.py
```

`seed_schemes.py` extracts text with `pypdf`, chunks it mechanically, embeds
chunks through local Ollama `nomic-embed-text`, and writes to
`scheme_documents` / `scheme_chunks`. This requires:

- `USE_LOCAL_MODELS=true`
- `nomic-embed-text` pulled in Ollama
- `migrations/0006_scheme_tables.sql` applied

## Required Manifest

The script refuses to infer scheme identity from filenames. Create
`manifest.json` in this directory:

```json
{
  "lakshmir_bhandar_guidelines.pdf": {
    "scheme_name": "Lakshmir Bhandar",
    "scheme_code": "LB",
    "document_type": "eligibility",
    "source_url": "https://<official-government-source-url>"
  }
}
```

PDFs missing from the manifest are skipped and reported.

## Source Policy

Only ingest official government PDFs from sources such as `wb.gov.in`,
`anandadhara.wb.gov.in`, or `wbfin.nic.in`. Do not seed from news articles,
SEO aggregator pages, or copied scheme summaries.

Before enabling scheme answers in production, re-review:

- Current official scheme validity and amounts.
- `services/rag_service/grounding_verifier.py`.
- Active graph routing.
- Migration state in the target database.
- End-to-end tests for refusal on ungrounded or stale claims.
