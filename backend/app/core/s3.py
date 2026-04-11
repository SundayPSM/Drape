"""
File storage via Supabase Storage (replaces AWS S3).
Bucket: drape-assets (must be created in Supabase Dashboard → Storage, set to Public)
"""
import uuid
import httpx
from storage3 import create_client as create_storage_client
from app.config import settings

BUCKET = "drape-assets"


def _storage_client():
    headers = {
        "apiKey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }
    return create_storage_client(
        url=f"{settings.supabase_url}/storage/v1",
        headers=headers,
        is_async=False,
    )


def generate_presigned_upload(prefix: str, content_type: str = "image/jpeg") -> dict:
    """
    Returns a Supabase signed upload URL for direct browser → Storage upload.
    The frontend should PUT the file to presigned.url with Content-Type header.
    """
    key = f"{prefix}/{uuid.uuid4()}.jpg"
    storage = _storage_client()
    result = storage.from_(BUCKET).create_signed_upload_url(key)
    # storage3 returns snake_case "signed_url" which is already a full URL
    signed_url = result["signed_url"]
    return {
        "key": key,
        "presigned": {
            "url": signed_url,
            "method": "PUT",
        },
    }


def get_public_url(key: str) -> str:
    """Return the public URL for an object in the public drape-assets bucket."""
    return f"{settings.supabase_url}/storage/v1/object/public/{BUCKET}/{key}"


def get_signed_url(key: str, expires: int = 3600) -> str:
    """Return a signed read URL for a private object."""
    storage = _storage_client()
    result = storage.from_(BUCKET).create_signed_url(key, expires)
    return result["signedURL"]


async def upload_bytes(data: bytes, prefix: str, content_type: str = "image/jpeg") -> str:
    """Upload raw bytes to Supabase Storage. Returns storage key."""
    key = f"{prefix}/{uuid.uuid4()}.jpg"
    storage = _storage_client()
    storage.from_(BUCKET).upload(
        path=key,
        file=data,
        file_options={"content-type": content_type},
    )
    return key


async def upload_from_url(source_url: str, prefix: str) -> str:
    """Download an image from a URL and upload to Supabase Storage. Returns storage key."""
    key = f"{prefix}/{uuid.uuid4()}.jpg"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(source_url)
        resp.raise_for_status()
        content = resp.content

    storage = _storage_client()
    storage.from_(BUCKET).upload(
        path=key,
        file=content,
        file_options={"content-type": "image/jpeg"},
    )
    return key
