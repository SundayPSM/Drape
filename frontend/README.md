# Drape — Frontend

Vue 3 frontend for the Drape AI Virtual Try-On platform.  
Paste any product URL, build a full outfit, pick a pose — AI generates a photorealistic result on your model.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Vue 3 (Composition API) |
| Build tool | Vite |
| Language | TypeScript |
| Styling | Tailwind CSS |
| State | Pinia |
| Routing | Vue Router 4 |
| HTTP | Axios |
| Auth | Supabase JS (Google OAuth) |

---

## Prerequisites

- Node.js 18+
- The Drape backend running locally or deployed
- A [Supabase](https://supabase.com) project with Google OAuth enabled

---

## Local Setup

### 1. Clone the repo

```bash
git clone https://github.com/SundayPSM/Drape-FE.git
cd Drape-FE
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Drape
VITE_APP_URL=http://localhost:5173

VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
```

> `VITE_API_BASE_URL` must point to your running backend.

### 4. Run the dev server

```bash
npm run dev
```

App runs at `http://localhost:5173`

---

## Project Structure

```
src/
├── views/
│   ├── LandingView.vue          # Marketing landing page
│   ├── DashboardView.vue        # Home after login
│   ├── OnboardingView.vue       # Upload reference photos + generate identity
│   ├── TryOnView.vue            # Outfit builder (garments + pose + generate)
│   ├── ResultView.vue           # Try-on result with compare slider
│   ├── ClosetView.vue           # All looks / saved looks gallery
│   ├── SettingsView.vue         # Profile settings
│   └── auth/
│       ├── LoginView.vue        # Login page
│       └── AuthCallbackView.vue # OAuth callback handler
├── components/
│   ├── layout/AppHeader.vue     # Top navigation
│   ├── results/CompareSlider.vue# Before/after drag slider
│   └── ui/                      # DrapeButton, DrapeSpinner, etc.
├── stores/
│   ├── auth.ts                  # Authentication state
│   ├── user.ts                  # User profile + identity
│   ├── tryon.ts                 # Try-on jobs + iterative layering state
│   └── ui.ts                    # Theme, toasts
├── services/
│   ├── api.ts                   # Axios instance (5 min timeout for AI calls)
│   ├── auth.service.ts          # Login / logout
│   ├── user.service.ts          # Profile, photos, identity
│   ├── product.service.ts       # URL extraction, quick-add
│   └── tryon.service.ts         # Submit, status, history, save
├── composables/
│   ├── useFileUpload.ts         # Presigned URL upload to Supabase Storage
│   └── useShare.ts              # Web Share API
├── router/index.ts              # Route definitions + auth guards
└── types/index.ts               # Shared TypeScript types
```

---

## App Flow

### 1. Onboarding (first time)
1. Sign in with Google
2. Fill in your profile — gender, age, height, weight, skin tone
3. Upload 6 guided reference photos (front, sides, full body)
4. AI generates your digital identity portrait (3-phase Gemini pipeline)
5. Pick your preferred portrait → set as active identity

### 2. Try-On
1. Go to **Build Your Outfit**
2. Paste product URLs into any garment slots (shirt, pants, jacket, shoes, watch, sunglasses)
3. For each garment, pick fit: **Slim / Regular / Oversized**
4. Optionally paste a **Pose Reference** image — AI copies the body pose and facial expression
5. Click **Generate Look →**
6. AI drapes the full outfit onto your model in ~20–40 seconds

### 3. Result
- View before/after compare slider
- **Save** to your closet
- **Download** the generated image
- **Share** via Web Share API
- **+ Add more to this look** — carries the result as the base for the next try-on (iterative layering)

### 4. My Looks
- Browse all generated try-ons
- Filter to saved looks
- Hover any card to download directly

---

## Build for Production

```bash
npm run build
```

Output is in `dist/` — deploy to any static host (Vercel, Netlify, Cloudflare Pages, etc.).

```bash
# Preview the production build locally
npm run preview
```

---

## Running with Docker

```bash
docker build -t drape-fe .
docker run -p 80:80 drape-fe
```

---

## Environment Variables Reference

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend API URL (e.g. `http://localhost:8000`) |
| `VITE_APP_TITLE` | App title shown in browser tab |
| `VITE_APP_URL` | Frontend public URL (for OAuth redirect) |
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |

---

## Notes

- AI generation requests can take **20–60 seconds** — the axios timeout is set to 5 minutes
- The Supabase storage bucket `drape-assets` must be **Public** for images to load
- Google OAuth redirect URL must be whitelisted in your Supabase project settings:  
  `http://localhost:5173/auth/callback` (dev) and your production URL
