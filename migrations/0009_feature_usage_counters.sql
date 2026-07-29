CREATE TABLE IF NOT EXISTS feature_usage_counters (
  user_id UUID NOT NULL,
  feature VARCHAR(30) NOT NULL,
  day_bucket DATE NOT NULL,
  use_count INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (user_id, feature, day_bucket)
);
CREATE INDEX IF NOT EXISTS idx_feature_usage_day ON feature_usage_counters(day_bucket);
