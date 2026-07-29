CREATE OR REPLACE FUNCTION prune_webhook_dedup() RETURNS TABLE(dedup_deleted BIGINT, rate_limit_deleted BIGINT) AS $$
DECLARE
  d_count BIGINT;
  r_count BIGINT;
BEGIN
  DELETE FROM webhook_dedup WHERE created_at < NOW() - INTERVAL '7 days';
  GET DIAGNOSTICS d_count = ROW_COUNT;

  DELETE FROM rate_limit_counters
    WHERE hour_bucket < (EXTRACT(EPOCH FROM NOW()) / 3600 - 168)::BIGINT;
  GET DIAGNOSTICS r_count = ROW_COUNT;

  RETURN QUERY SELECT d_count, r_count;
END;
$$ LANGUAGE plpgsql;
