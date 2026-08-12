



DELETE FROM webhook_dedup
WHERE created_at < NOW() - INTERVAL '7 days';








