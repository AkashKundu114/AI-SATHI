CREATE TABLE IF NOT EXISTS webhook_dedup (
  message_id VARCHAR(255) PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_webhook_dedup_created_at ON webhook_dedup(created_at);

CREATE TABLE IF NOT EXISTS rate_limit_counters (
  phone_number VARCHAR(20) NOT NULL,
  hour_bucket BIGINT NOT NULL,
  message_count INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (phone_number, hour_bucket)
);
