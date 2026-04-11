-- B2C v1.1: Trust layer columns on tryon_jobs
ALTER TABLE tryon_jobs ADD COLUMN IF NOT EXISTS fit_confidence FLOAT;
ALTER TABLE tryon_jobs ADD COLUMN IF NOT EXISTS fit_notes TEXT;
