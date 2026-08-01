CREATE TABLE IF NOT EXISTS response_cache (
  cache_key VARCHAR(300) PRIMARY KEY,
  response_text TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_response_cache_created_at ON response_cache(created_at);

CREATE TABLE IF NOT EXISTS poster_dedup_cache (
  dedup_key VARCHAR(300) PRIMARY KEY,
  poster_s3_key VARCHAR(500) NOT NULL,
  poster_tier VARCHAR(20) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
