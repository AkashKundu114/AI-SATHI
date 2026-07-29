CREATE TABLE IF NOT EXISTS api_usage_monthly (
  user_id       UUID NOT NULL,
  provider      VARCHAR(30) NOT NULL,
  month_bucket  VARCHAR(7) NOT NULL,
  call_count    INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (user_id, provider, month_bucket)
);
CREATE INDEX IF NOT EXISTS idx_api_usage_month ON api_usage_monthly(month_bucket);

CREATE TABLE IF NOT EXISTS user_plans (
  user_id       UUID PRIMARY KEY REFERENCES users(id),
  plan_tier     VARCHAR(20) NOT NULL DEFAULT 'free',
  plan_expires  TIMESTAMPTZ,
  upgraded_at   TIMESTAMPTZ,
  payment_ref   VARCHAR(255),
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
