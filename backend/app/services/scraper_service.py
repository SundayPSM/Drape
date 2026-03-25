"""
Product scraper using Playwright + Open Graph / JSON-LD extraction.
"""
import re
import json
import uuid
import httpx
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup

from app.core.s3 import upload_from_url, get_public_url
from app.core.exceptions import DomainError


class ScrapedProduct:
    def __init__(self, name: str, brand: str | None, description: str | None,
                 price: float | None, currency: str, image_url: str | None,
                 source_url: str):
        self.name = name
        self.brand = brand
        self.description = description
        self.price = price
        self.currency = currency
        self.image_url = image_url
        self.source_url = source_url
        self.image_s3_key: str | None = None


async def scrape_product(url: str) -> ScrapedProduct:
    """
    Scrape product details from a retailer URL.
    Priority: JSON-LD → Open Graph → DOM heuristics
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            await page.goto(url, wait_until="networkidle", timeout=30000)
            html = await page.content()
        finally:
            await browser.close()

    soup = BeautifulSoup(html, "lxml")

    # Try JSON-LD first
    product = _extract_json_ld(soup, url)
    if not product:
        product = _extract_open_graph(soup, url)
    if not product:
        raise DomainError("Could not extract product information from this URL. Try a different product page.", 422)

    # Upload image to S3
    if product.image_url:
        try:
            product.image_s3_key = await upload_from_url(product.image_url, prefix="products")
        except Exception:
            pass  # Non-fatal: keep original URL

    return product


def _extract_json_ld(soup: BeautifulSoup, url: str) -> ScrapedProduct | None:
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                data = next((d for d in data if d.get("@type") == "Product"), None)
            if not data or data.get("@type") != "Product":
                continue

            name = data.get("name", "")
            if not name:
                continue

            brand = None
            if isinstance(data.get("brand"), dict):
                brand = data["brand"].get("name")
            elif isinstance(data.get("brand"), str):
                brand = data["brand"]

            price = None
            currency = "USD"
            offers = data.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            if offers:
                try:
                    price = float(str(offers.get("price", "")).replace(",", ""))
                except (ValueError, TypeError):
                    pass
                currency = offers.get("priceCurrency", "USD")

            image = data.get("image")
            if isinstance(image, list):
                image = image[0]
            if isinstance(image, dict):
                image = image.get("url")

            return ScrapedProduct(
                name=name,
                brand=brand,
                description=data.get("description"),
                price=price,
                currency=currency,
                image_url=image,
                source_url=url,
            )
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


def _extract_open_graph(soup: BeautifulSoup, url: str) -> ScrapedProduct | None:
    def og(prop: str) -> str | None:
        tag = soup.find("meta", property=f"og:{prop}") or soup.find("meta", attrs={"name": f"og:{prop}"})
        return tag.get("content") if tag else None  # type: ignore

    title = og("title") or (soup.title.string if soup.title else None)
    if not title:
        return None

    image = og("image")
    description = og("description")

    # Try to parse price from page
    price = None
    price_meta = soup.find("meta", property="product:price:amount") or soup.find("meta", attrs={"name": "price"})
    if price_meta:
        try:
            price = float(str(price_meta.get("content", "")).replace(",", ""))
        except (ValueError, TypeError):
            pass

    return ScrapedProduct(
        name=title,
        brand=_extract_brand(soup, url),
        description=description,
        price=price,
        currency="USD",
        image_url=image,
        source_url=url,
    )


def _extract_brand(soup: BeautifulSoup, url: str) -> str | None:
    # Try meta tags
    for name in ["brand", "og:brand", "product:brand"]:
        tag = soup.find("meta", property=name) or soup.find("meta", attrs={"name": name})
        if tag:
            return tag.get("content")  # type: ignore
    # Fallback: extract from domain
    domain = urlparse(url).netloc.replace("www.", "")
    return domain.split(".")[0].title() if domain else None
