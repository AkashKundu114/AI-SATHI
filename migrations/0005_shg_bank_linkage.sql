-- Backs the bank-loan-grade PDF additions (generator.py now renders SHG
-- grading + bank-linkage status alongside the P&L, per the original v1 TRD
-- schema's shg_groups.bank_linkage_status which the v2/v3 rewrite dropped
-- when the table was re-declared in migrations/0001_init.sql. Additive
-- only, safe to run against an existing DB.

ALTER TABLE shg_groups ADD COLUMN IF NOT EXISTS bank_linkage_status VARCHAR(50);
-- Expected values: NONE, PHASE1, PHASE2, PHASE3 (matches the original TRD's
-- West Bengal SHG bank-linkage phase convention). Not enforced with a CHECK
-- constraint here — same permissive-varchar style already used for
-- entry_type/data_source elsewhere in this schema, so a new phase name
-- doesn't require a migration to add.
