import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.base import get_db
from app.db.models.product import Product, ProductCategory
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.product import ProductResponse, ScrapeRequest, ProductListResponse
from app.services.scraper_service import scrape_product

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
