-- Fixes a documented bug: migrations/0002_hybrid_search.sql runs
-- `ALTER TABLE scheme_chunks ADD COLUMN ...`, but no prior migration ever
-- `CREATE TABLE`s scheme_chunks (or its parent scheme_documents) -- see
-- DELETE_LIST.md section C: "this code is currently undeployable, not just
-- unrouted." This migration supplies the missing DDL, matching the
-- original schema documented in docs/archive/product/trd.md §3.5, adapted
-- to this repo's actual conventions (gen_random_uuid() via pgcrypto,
-- already enabled in 0001_init.sql).
--
-- Ordering: must run AFTER 0001_init.sql (no dependency on it directly,
-- but pgcrypto's gen_random_uuid() needs to already be enabled, which
-- 0001 does) and BEFORE 0002_hybrid_search.sql's ALTER TABLE actually
-- succeeds. Since this file is numbered 0006, it will NOT run before
-- 0002 in a fresh `docker-entrypoint-initdb.d` alphabetical/numeric
-- ordering -- confirm your deploy script applies migrations in an order
-- that tolerates this, or renumber before applying to a fresh database.
-- (On an EXISTING database, 0002 has presumably already failed loudly at
-- deploy time -- that failure is itself the signal this migration exists
-- to fix; this file is safe to apply any time before you actually need
-- scheme_chunks to work.)

CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector, per docs/architecture.md's
                                          -- "pgvector co-located with Postgres" decision

CREATE TABLE IF NOT EXISTS scheme_documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scheme_name VARCHAR(255) NOT NULL,
  scheme_code VARCHAR(50),
  document_type VARCHAR(50), -- 'eligibility', 'benefits', 'application_process', 'documents_required'
  content_bengali TEXT,
  content_english TEXT,
  source_url VARCHAR(500),
  source_file VARCHAR(500),  -- local filename under data/schemes/raw/, for audit trail
  last_verified_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scheme_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES scheme_documents(id) ON DELETE CASCADE,
  chunk_text TEXT NOT NULL,
  chunk_bengali TEXT,
  embedding vector(768),  -- nomic-embed-text via Ollama (768-dim), matching
                           -- shared/config/settings.py's ollama_* fields and
                           -- rag_service/pipeline.py's get_embedding() --
                           -- NOT 1536 (that was the abandoned OpenAI
                           -- text-embedding-3-small dimension from the v1
                           -- plan; this repo has no OpenAI dependency, see
                           -- docs/architecture.md §8)
  chunk_index INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheme_chunks_document ON scheme_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_scheme_chunks_embedding ON scheme_chunks
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- ivfflat needs at least a handful of rows to build a meaningful index;
-- harmless but low-value on an empty/near-empty table. Fine for this
-- product's scale (PRD: ≤ 1M scheme document chunks) per docs/architecture.md.

-- 0002_hybrid_search.sql's ALTER TABLE / generated tsvector column and GIN
-- index will now succeed against this table, closing the gap. Not
-- repeated here -- 0002 stays the single source for that specific DDL.
