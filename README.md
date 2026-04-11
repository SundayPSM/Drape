# Drape — AI Virtual Try-On Platform

Drape lets users virtually try on clothing, accessories, and full outfits using AI. Upload your photo, pick a garment, and see yourself wearing it in seconds — powered by Google Gemini.

---

## Features

- AI-powered virtual try-on using Google Gemini image generation
- Multi-garment outfits — tops, bottoms, outerwear, footwear, watches, sunglasses simultaneously
- Pose reference — paste any photo URL, AI copies the pose and expression
- Iterative layering — add a jacket on top of your existing result, then add shoes on top of that
- Fit selector — Slim, Regular, or Oversized per garment
- Closet gallery — all your try-ons in one place with download and save
- Google OAuth via Supabase
- Affiliate buy links on results

---

## Project Structure

```
Drape/
├── backend/          # FastAPI — AI pipeline, REST API, Supabase DB
├── frontend/         # Vue 3 — user interface
├── infra/            # DB migration scripts
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/SundayPSM/Drape.git
cd Drape
```

### 2. Set up environment variables

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` with your credentials:

| Variable | Where to get it |
|---|---|
| `DATABASE_URL` | Supabase → Project Settings → Database |
| `SUPABASE_URL` | Supabase → Project Settings → API |
| `SUPABASE_ANON_KEY` | Supabase → Project Settings → API |
| `SUPABASE_JWT_SECRET` | Supabase → Project Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API |
| `GOOGLE_API_KEY` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |

Edit `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

---

## Running with Docker (recommended)

Runs backend + frontend + Redis together:

```bash
docker-compose up --build
```

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running Locally (without Docker)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Database Setup

Run the migration scripts in order:

```bash
psql $DATABASE_URL -f infra/scripts/create_tables.sql
psql $DATABASE_URL -f infra/scripts/add_profile_fields.sql
```

Or run them in Supabase → SQL Editor.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/users/me` | Get current user profile |
| `PUT` | `/api/v1/users/me` | Update profile |
| `POST` | `/api/v1/users/me/identity` | Generate AI identity |
| `GET` | `/api/v1/products` | List curated products |
| `POST` | `/api/v1/products` | Add a product |
| `POST` | `/api/v1/tryon/submit` | Submit try-on job |
| `GET` | `/api/v1/tryon/{job_id}` | Get job status + result |
| `GET` | `/api/v1/tryon/history` | All try-ons for user |

---

## Tech Stack

**Backend**
- Python 3.11, FastAPI, SQLAlchemy (async), asyncpg
- Google Gemini (`gemini-2.0-flash-preview-image-generation`) for AI generation
- Supabase — PostgreSQL database + Storage + Google OAuth
- Redis (optional, for future task queue)

**Frontend**
- Vue 3 (Composition API), TypeScript
- Pinia (state management), Vue Router
- Tailwind CSS
- Axios

---

## Deployment

**Backend** — Deploy to Railway, Render, or any Docker host. Set all env vars from `.env.example`.

**Frontend** — Deploy to Vercel or Netlify:
```bash
cd frontend
npm run build
# deploy the dist/ folder
```

Update `VITE_API_BASE_URL` in frontend env to point to your deployed backend URL.
