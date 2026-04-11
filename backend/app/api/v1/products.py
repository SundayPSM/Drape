import uuid
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.base import get_db
from app.db.models.product import Product, ProductCategory
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.product import (
    ProductResponse, ScrapeRequest, ProductListResponse,
    ExtractImageRequest, ExtractImageResponse, QuickAddRequest,
)
from app.services.scraper_service import scrape_product
from app.core.exceptions import DomainError

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    category: ProductCategory | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Product).where(Product.is_active == True)  # noqa: E712
    if category:
        stmt = stmt.where(Product.category == category)
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = list(await db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)))

    return ProductListResponse(
        items=items,
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    product = await db.get(Product, product_id)
    if not product or not product.is_active:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Product")
    return product


_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif', '.jfif', '.bmp'}
_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


@router.post("/extract-image", response_model=ExtractImageResponse)
async def extract_image(
    data: ExtractImageRequest,
    _: User = Depends(get_current_user),
):
    """Extract a product image from any URL — direct image or product page."""
    url = data.url.strip()
    parsed = urlparse(url)
    path = parsed.path.lower().split("?")[0]

    # Direct image URL — return immediately
    if any(path.endswith(ext) for ext in _IMAGE_EXTS):
        return ExtractImageResponse(image_url=url, title=None, source_url=url)

    # Product page — extract og:image via httpx
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers=_HEADERS)
            resp.raise_for_status()
    except Exception as exc:
        raise DomainError(f"Could not fetch URL: {exc}", 422)

    soup = BeautifulSoup(resp.text, "lxml")

    og_image = soup.find("meta", property="og:image")
    image_url = og_image.get("content") if og_image else None  # type: ignore

    if not image_url:
        # Try twitter:image as fallback
        tw_image = soup.find("meta", attrs={"name": "twitter:image"})
        image_url = tw_image.get("content") if tw_image else None  # type: ignore

    if not image_url:
        raise DomainError("Could not extract an image from this URL. Try pasting the direct image URL.", 422)

    og_title = soup.find("meta", property="og:title")
    title = (og_title.get("content") if og_title else None) or (soup.title.string if soup.title else None)  # type: ignore

    return ExtractImageResponse(image_url=image_url, title=title, source_url=url)


@router.post("/quick-add", response_model=ProductResponse, status_code=201)
async def quick_add_product(
    data: QuickAddRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a product from a pasted image URL without full scraping."""
    product = Product(
        name=data.name or "Custom Garment",
        category=data.category,
        image_url=data.image_url,
        source_url=data.source_url,
        is_active=True,
        is_curated=False,
        currency="USD",
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


@router.post("/scrape", response_model=ProductResponse, status_code=201)
async def scrape_product_url(
    data: ScrapeRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Scrape a product from any e-commerce URL and add to catalog."""
    scraped = await scrape_product(data.url)

    product = Product(
        name=scraped.name,
        brand=scraped.brand,
        description=scraped.description,
        price=scraped.price,
        currency=scraped.currency,
        image_url=scraped.image_url,
        image_s3_key=scraped.image_s3_key,
        source_url=scraped.source_url,
        is_active=True,
        is_curated=False,
    )
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product
