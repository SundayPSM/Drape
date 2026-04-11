# Drape — Backend

FastAPI backend for the Drape AI Virtual Try-On platform.  
Powered by **Google Gemini** for image generation, **Supabase** for auth and storage, and **PostgreSQL** for the database.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI (async) |
| Database | PostgreSQL via Supabase (asyncpg + SQLAlchemy) |
| Migrations | Alembic |
| Auth | Google OAuth via Supabase JWT |
| Storage | Supabase Storage |
| AI | Google Gemini `gemini-3.1-flash-image-preview` |
| HTTP client | httpx |
| Scraping | BeautifulSoup4 |

---

## Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project (database + storage + Google OAuth enabled)
- A [Google AI Studio](https://aistudio.google.com/apikey) API key

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/SundayPSM/Drape-BE.git
cd Drape-BE
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
# venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in all values:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

DEBUG=True
APP_URL=http://localhost:8000
ALLOWED_ORIGINS=["http://localhost:5173"]

REDIS_URL=redis://localhost:6379/0

GOOGLE_API_KEY=your_google_api_key
```

### 5. Set up the database

Run the SQL scripts in your Supabase SQL Editor (Dashboard → SQL Editor):

```sql
-- Create all tables
-- See: infra/scripts/create_tables.sql

-- Add profile fields if upgrading
-- See: infra/scripts/add_profile_fields.sql
```

Or run Alembic migrations if you have migration files:

```bash
alembic upgrade head
```

### 6. Set up Supabase Storage

In your Supabase Dashboard → Storage:
1. Create a bucket named **`drape-assets`**
2. Set it to **Public**

### 7. Run the server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## Project Structure

```
app/
├── api/
│   └── v1/
│       ├── auth.py          # Google OAuth callback
│       ├── users.py         # Profile, photos, identity generation
│       ├── products.py      # Product CRUD, URL image extraction
│       └── tryon.py         # Try-on submit, status, history
├── core/
│   ├── gemini.py            # AI image generation (all prompts live here)
│   ├── s3.py                # Supabase Storage helpers
│   ├── security.py          # JWT verification
│   └── exceptions.py        # Domain error classes
├── db/
│   ├── models/              # SQLAlchemy ORM models
│   └── base.py              # Async session factory
├── schemas/                 # Pydantic request/response models
├── services/
│   ├── identity_service.py  # 3-phase AI portrait pipeline
│   └── tryon_service.py     # Try-on orchestration
├── config.py                # Settings (loaded from .env)
└── main.py                  # FastAPI app entry point
```

---

## Key API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/google` | Exchange Supabase token for session |
| `GET` | `/api/v1/users/me` | Get current user profile |
| `PATCH` | `/api/v1/users/me` | Update profile (height, weight, etc.) |
| `POST` | `/api/v1/users/me/photos/upload-url` | Get presigned URL to upload a reference photo |
| `POST` | `/api/v1/users/me/identity/generate` | Run AI identity generation pipeline |
| `POST` | `/api/v1/products/extract-image` | Extract garment image from any URL |
| `POST` | `/api/v1/products/quick-add` | Create a product from extracted image |
| `POST` | `/api/v1/tryon/submit` | Submit a try-on job |
| `GET` | `/api/v1/tryon/{job_id}/status` | Poll job status |
| `GET` | `/api/v1/tryon/history` | Get user's try-on history |
| `PATCH` | `/api/v1/tryon/{job_id}/save` | Save a look to closet |

---

## AI Pipeline Overview

### Identity Generation (3 phases)
1. **Phase 0** — Analyze 6 uploaded reference photos → detect body type
2. **Phase 1** — Generate 10 synthetic angle variations from the 6 originals
3. **Phase 2** — Generate 4 final try-on portrait candidates → user picks one

### Try-On Generation
- Accepts 1–6 garments simultaneously (shirt + pants + jacket + shoes + watch + sunglasses)
- Optional pose reference image — AI copies body pose and facial expression
- Optional base image — previous result is used for iterative layering
- Per-garment: category-specific fabric physics + fit type (slim / regular / oversized)
- Subject physical profile (height, weight, gender, body type) anchored in every prompt

---

## Running with Docker

```bash
docker build -t drape-be .
docker run -p 8000:8000 --env-file .env drape-be
```

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg format) |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon/public key |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret (for token verification) |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (for storage) |
| `GOOGLE_API_KEY` | Google AI Studio API key (Gemini) |
| `APP_URL` | Public URL of this backend (used for webhooks) |
| `ALLOWED_ORIGINS` | JSON array of allowed CORS origins |
| `DEBUG` | `True` for development, `False` for production |
| `REDIS_URL` | Redis connection string (for Celery tasks) |
