"""
Verify Supabase-issued JWTs.
Supabase signs tokens with HS256 using the project JWT secret.
No custom token minting — Supabase Auth handles that entirely.
"""
from jose import jwt, JWTError
from app.config import settings


def decode_supabase_token(token: str) -> dict:
    """
    Verify and decode a Supabase JWT.
    Returns the payload dict, or empty dict if invalid.
    The 'sub' field is the Supabase user UUID (str).
    The 'email' field is the user's email.
    """
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError:
        return {}
