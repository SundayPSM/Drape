-- Add body profile fields to users table
-- Run in: Supabase Dashboard → SQL Editor → New query

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS gender      VARCHAR(30),
    ADD COLUMN IF NOT EXISTS age         SMALLINT,
    ADD COLUMN IF NOT EXISTS height_cm   SMALLINT,
    ADD COLUMN IF NOT EXISTS weight_kg   SMALLINT,
    ADD COLUMN IF NOT EXISTS usual_size  VARCHAR(10),
    ADD COLUMN IF NOT EXISTS skin_tone   VARCHAR(20),
    ADD COLUMN IF NOT EXISTS body_type   VARCHAR(30);

SELECT 'Profile fields added to users table!' AS result;
