from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.db.models.user import User
from app.core.security import decode_supabase_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_supabase_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supabase_id = payload.get("sub")
    email = payload.get("email", "")
    # Google OAuth stores name in user_metadata
    user_metadata = payload.get("user_metadata", {})
    name = user_metadata.get("full_name") or user_metadata.get("name") or email.split("@")[0]
    avatar_url = user_metadata.get("avatar_url") or user_metadata.get("picture")

    if not supabase_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")

    # Upsert: create user record on first login, update metadata on subsequent logins
    user = await db.scalar(select(User).where(User.supabase_id == supabase_id))
    if not user:
        user = User(
            supabase_id=supabase_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    else:
        # Keep name/avatar fresh from Google
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
        await db.flush()

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled")

    return user
