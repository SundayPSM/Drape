-- Drape — Create all tables in Supabase
-- Run this in: Supabase Dashboard → SQL Editor → New query

-- Enable UUID extension (already enabled on Supabase by default)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Users ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_id VARCHAR(100) NOT NULL UNIQUE,
    email       VARCHAR(255) NOT NULL UNIQUE,
    name        VARCHAR(100) NOT NULL,
    avatar_url  VARCHAR(500),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_supabase_id ON users(supabase_id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- ─── User Photos ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_photos (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    s3_key      VARCHAR(500) NOT NULL,
    photo_type  VARCHAR(50) NOT NULL DEFAULT 'general',
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── User Identities ──────────────────────────────────────────────────────────
CREATE TYPE identity_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS user_identities (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status                  identity_status NOT NULL DEFAULT 'pending',
    s3_key                  VARCHAR(500),
    source_photo_ids        VARCHAR(1000),
    replicate_prediction_id VARCHAR(100),
    error_message           VARCHAR(500),
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Products ─────────────────────────────────────────────────────────────────
CREATE TYPE product_category AS ENUM (
    'tops', 'bottoms', 'dresses', 'outerwear',
    'footwear', 'accessories', 'watches', 'sunglasses'
);

CREATE TABLE IF NOT EXISTS products (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name              VARCHAR(300) NOT NULL,
    brand             VARCHAR(100),
    description       TEXT,
    category          product_category NOT NULL DEFAULT 'tops',
    price             FLOAT,
    currency          VARCHAR(3) NOT NULL DEFAULT 'USD',
    image_s3_key      VARCHAR(500),
    image_url         VARCHAR(1000),
    source_url        VARCHAR(1000),
    affiliate_url     VARCHAR(1000),
    affiliate_network VARCHAR(100),
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    is_curated        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Try-On Jobs ──────────────────────────────────────────────────────────────
CREATE TYPE tryon_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS tryon_jobs (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id              UUID NOT NULL REFERENCES products(id),
    identity_id             UUID NOT NULL REFERENCES user_identities(id),
    replicate_prediction_id VARCHAR(100),
    status                  tryon_status NOT NULL DEFAULT 'pending',
    human_img_url           VARCHAR(1000),
    garment_img_url         VARCHAR(1000),
    result_s3_key           VARCHAR(500),
    result_url              VARCHAR(1000),
    error_message           TEXT,
    is_saved                BOOLEAN NOT NULL DEFAULT FALSE,
    share_slug              VARCHAR(50) UNIQUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at            TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_tryon_jobs_user_id ON tryon_jobs(user_id);
CREATE INDEX IF NOT EXISTS ix_tryon_jobs_prediction_id ON tryon_jobs(replicate_prediction_id);

-- ─── Seed: Sample products ────────────────────────────────────────────────────
INSERT INTO products (name, brand, description, category, price, currency, image_url, is_active, is_curated)
VALUES
    ('Classic White Oxford Shirt', 'Drape Essentials', 'A crisp white Oxford shirt with a relaxed fit and button-down collar.', 'tops', 89.00, 'USD', 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800', TRUE, TRUE),
    ('Navy Linen Blazer', 'Drape Studio', 'Lightweight navy linen blazer, perfect for summer evenings.', 'outerwear', 245.00, 'USD', 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800', TRUE, TRUE),
    ('Silk Slip Dress', 'Atelier Drape', 'Minimalist silk-touch slip dress in champagne. Effortlessly elegant.', 'dresses', 195.00, 'USD', 'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800', TRUE, TRUE),
    ('Black Turtleneck Sweater', 'Drape Basics', 'Fine-knit merino wool turtleneck in classic black.', 'tops', 120.00, 'USD', 'https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=800', TRUE, TRUE),
    ('Camel Wool Overcoat', 'Drape Studio', 'Structured camel-toned wool overcoat with clean lapels.', 'outerwear', 420.00, 'USD', 'https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=800', TRUE, TRUE),
    ('White Graphic Tee', 'Drape Basics', 'Premium cotton oversized graphic tee with minimal branding.', 'tops', 45.00, 'USD', 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800', TRUE, TRUE)
ON CONFLICT DO NOTHING;

SELECT 'All tables created and catalog seeded!' AS result;
