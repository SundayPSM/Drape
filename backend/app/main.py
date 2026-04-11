from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.router import router
from app.db.base import engine
from app.core.exceptions import DomainError


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are created via Supabase dashboard / Alembic migrations
    # No auto-DDL here
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# ─── Routes ───────────────────────────────────────────────────────────────────

app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}


@app.post("/debug/token")
async def debug_token(request: Request):
    """Temporary: decode a Supabase token and show the result. Remove before prod."""
    from app.core.security import decode_supabase_token
    body = await request.json()
    token = body.get("token", "")
    payload = decode_supabase_token(token)
    return {
        "decoded": bool(payload),
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "aud": payload.get("aud"),
        "alg": payload.get("_claim_names"),
    }
