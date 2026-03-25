import uuid
import httpx
import boto3
from botocore.exceptions import ClientError
from app.config import settings


def _s3_client():
    kwargs = dict(
        region_name=settings.aws_s3_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )
    if settings.aws_s3_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_s3_endpoint_url
    return boto3.client("s3", **kwargs)


def generate_presigned_upload(prefix: str, content_type: str = "image/jpeg") -> dict:
    """Return presigned POST data for direct browser → S3 upload."""
    key = f"{prefix}/{uuid.uuid4()}.jpg"
    s3 = _s3_client()
    data = s3.generate_presigned_post(
        Bucket=settings.aws_s3_bucket,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, 20_000_000],  # 20 MB max
        ],
        ExpiresIn=300,
    )
    return {"key": key, "presigned": data}


def get_public_url(key: str) -> str:
    """Return the public URL for an S3 object."""
    if settings.aws_s3_endpoint_url:
        return f"{settings.aws_s3_endpoint_url}/{settings.aws_s3_bucket}/{key}"
    return f"https://{settings.aws_s3_bucket}.s3.{settings.aws_s3_region}.amazonaws.com/{key}"


def generate_presigned_get(key: str, expires: int = 3600) -> str:
    """Return a presigned GET URL for private objects."""
    s3 = _s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.aws_s3_bucket, "Key": key},
        ExpiresIn=expires,
    )


async def upload_from_url(source_url: str, prefix: str) -> str:
    """Download an image from a URL and upload to S3. Returns S3 key."""
    key = f"{prefix}/{uuid.uuid4()}.jpg"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(source_url)
        resp.raise_for_status()
        content = resp.content

    s3 = _s3_client()
    s3.put_object(
        Bucket=settings.aws_s3_bucket,
        Key=key,
        Body=content,
        ContentType="image/jpeg",
        ACL="public-read",
    )
    return key
