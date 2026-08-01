CREATE TABLE IF NOT EXISTS credit_budget (
  vendor VARCHAR(30) PRIMARY KEY,
  total_budget NUMERIC(10,2) NOT NULL,
  used NUMERIC(10,2) NOT NULL DEFAULT 0,
  degraded_mode BOOLEAN NOT NULL DEFAULT FALSE,
  hard_stopped BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO credit_budget (vendor, total_budget) VALUES ('sarvam', 1000)
  ON CONFLICT (vendor) DO NOTHING;
INSERT INTO credit_budget (vendor, total_budget) VALUES ('flux', 1000)
  ON CONFLICT (vendor) DO NOTHING;

CREATE TABLE IF NOT EXISTS credit_usage_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vendor VARCHAR(30) NOT NULL,
  call_type VARCHAR(30) NOT NULL,
  credits_charged NUMERIC(6,2) NOT NULL,
  user_id UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_credit_usage_log_created_at ON credit_usage_log(created_at);
CREATE INDEX IF NOT EXISTS idx_credit_usage_log_user ON credit_usage_log(user_id, created_at);
