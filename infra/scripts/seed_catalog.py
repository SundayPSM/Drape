"""
Seed the product catalog with curated items for demo/MVP.
Run: python infra/scripts/seed_catalog.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from app.db.base import AsyncSessionFactory, engine, Base
from app.db.models.product import Product, ProductCategory


SAMPLE_PRODUCTS = [
    {
        "name": "Classic White Oxford Shirt",
        "brand": "Drape Essentials",
        "description": "A crisp white Oxford shirt with a relaxed fit and button-down collar.",
        "category": ProductCategory.tops,
        "price": 89.00,
        "currency": "USD",
        "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800",
        "is_curated": True,
    },
    {
        "name": "Navy Linen Blazer",
        "brand": "Drape Studio",
        "description": "Lightweight navy linen blazer, perfect for summer evenings.",
        "category": ProductCategory.outerwear,
        "price": 245.00,
        "currency": "USD",
        "image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800",
        "is_curated": True,
    },
    {
        "name": "Silk Slip Dress",
        "brand": "Atelier Drape",
        "description": "Minimalist silk-touch slip dress in champagne. Effortlessly elegant.",
        "category": ProductCategory.dresses,
        "price": 195.00,
        "currency": "USD",
        "image_url": "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=800",
        "is_curated": True,
    },
    {
        "name": "Black Turtleneck Sweater",
        "brand": "Drape Basics",
        "description": "Fine-knit merino wool turtleneck in classic black.",
        "category": ProductCategory.tops,
        "price": 120.00,
        "currency": "USD",
        "image_url": "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=800",
        "is_curated": True,
    },
    {
        "name": "Camel Wool Overcoat",
        "brand": "Drape Studio",
        "description": "Structured camel-toned wool overcoat with clean lapels.",
        "category": ProductCategory.outerwear,
        "price": 420.00,
        "currency": "USD",
        "image_url": "https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=800",
        "is_curated": True,
    },
    {
        "name": "White Graphic Tee",
        "brand": "Drape Basics",
        "description": "Premium cotton oversized graphic tee with minimal branding.",
        "category": ProductCategory.tops,
        "price": 45.00,
        "currency": "USD",
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800",
        "is_curated": True,
    },
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionFactory() as db:
        for item in SAMPLE_PRODUCTS:
            product = Product(**item)
            db.add(product)
        await db.commit()
        print(f"Seeded {len(SAMPLE_PRODUCTS)} products.")


if __name__ == "__main__":
    asyncio.run(seed())
