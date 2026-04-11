import httpx
from jose import jwt, JWTError
from app.config import settings

# Cache JWKS in memory (fetched once per process start)
_jwks_cache: dict | None = None

SUPABASE_JWKS_URL = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        response = httpx.get(SUPABASE_JWKS_URL, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def decode_supabase_token(token: str) -> dict:
    """
    Verify and decode a Supabase JWT.
    Tries JWKS (ES256/RS256) first, then falls back to HS256 JWT secret.
    Returns the payload dict, or empty dict if invalid.
    """
    e1: Exception | None = None

    # --- Try asymmetric key via JWKS ---
    try:
        jwks = _get_jwks()
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        alg = header.get("alg", "ES256")

        # Find the matching key in the key set
        matching_key = None
        for k in jwks.get("keys", []):
            if not kid or k.get("kid") == kid:
                matching_key = k
                break

        if matching_key:
            payload = jwt.decode(
                token,
                matching_key,
                algorithms=[alg],
                options={"verify_aud": False},
            )
            return payload
        else:
            e1 = ValueError(f"No matching key found for kid={kid} in JWKS")
    except Exception as exc:
        e1 = exc

    # --- Fallback: HS256 with the JWT secret ---
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e2:
        print(f"[JWT ERROR] JWKS attempt: {e1} | HS256 fallback: {e2}")
        print(f"[JWT DEBUG] Token prefix: {token[:40]}...")
        return {}
