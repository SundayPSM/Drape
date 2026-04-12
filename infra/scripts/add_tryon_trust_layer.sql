-- B2C v1.1: Trust layer columns on tryon_jobs
ALTER TABLE tryon_jobs ADD COLUMN IF NOT EXISTS fit_confidence FLOAT;
ALTER TABLE tryon_jobs ADD COLUMN IF NOT EXISTS fit_notes TEXT;

-- v1.1 enhanced trust layer
ALTER TABLE tryon_jobs ADD COLUMN IF NOT EXISTS fit_confidence_pct INTEGER;
ALTER TABLE tryon_jobs ADD COLUMN IF NOT EXISTS suggested_size VARCHAR(10);
ALTER TABLE tryon_jobs ADD COLUMN IF NOT EXISTS fit_type VARCHAR(100);
