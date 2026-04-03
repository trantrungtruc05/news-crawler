"""Crawl TechCrunch category/tag pages for article data."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup, Tag

from news_crawler.core.config import settings
from news_crawler.core.exceptions import CrawlerError
from news_crawler.models.article import ArticleData

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_article_links(
    base_url: str,
    max_pages: int | None = None,
) -> list[str]:
    """Fetch article URLs from a TechCrunch listing page.

    Args:
        base_url: The category or tag listing URL.
        max_pages: Number of listing pages to scan. Defaults to config value.

    Returns:
        Deduplicated list of article URLs.

    Raises:
        CrawlerError: If the listing page cannot be fetched.
    """
    max_pages = max_pages or settings.crawl_max_pages
    urls: list[str] = []

    for page in range(1, max_pages + 1):
        page_url = base_url
        if page > 1:
            page_url = f"{base_url.rstrip('/')}/page/{page}/"

        logger.info("Fetching listing page %d: %s", page, page_url)

        try:
            response = httpx.get(
                page_url,
                headers=HEADERS,
                timeout=settings.crawl_timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("Failed to fetch listing page %d", page)
            raise CrawlerError(
                f"Cannot fetch listing page {page}: {exc}"
            ) from exc

        soup = BeautifulSoup(response.text, "lxml")
        links = _extract_links_from_listing(soup)
        logger.info("Found %d article links on page %d", len(links), page)
        urls.extend(links)

    unique_urls = list(dict.fromkeys(urls))
    logger.info("Total unique article URLs: %d", len(unique_urls))
    return unique_urls


def scrape_article(url: str, category: str) -> ArticleData:
    """Scrape a single TechCrunch article page.

    Args:
        url: The full URL of the article.
        category: The category this article belongs to.

    Returns:
        Parsed article data.

    Raises:
        CrawlerError: If the article page cannot be fetched or parsed.
    """
    logger.info("Scraping article [%s]: %s", category, url)

    try:
        response = httpx.get(
            url,
            headers=HEADERS,
            timeout=settings.crawl_timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Failed to fetch article: %s", url)
        raise CrawlerError(f"Cannot fetch article {url}: {exc}") from exc

    soup = BeautifulSoup(response.text, "lxml")

    try:
        return _parse_article(soup, url, category)
    except Exception as exc:
        logger.exception("Failed to parse article: %s", url)
        raise CrawlerError(f"Cannot parse article {url}: {exc}") from exc


def _extract_links_from_listing(soup: BeautifulSoup) -> list[str]:
    links: list[str] = []
    for heading in soup.select("h2 a, h3 a"):
        href = heading.get("href")
        if href and "techcrunch.com" in str(href) and "/20" in str(href):
            links.append(str(href))
    return links


def _parse_article(
    soup: BeautifulSoup, url: str, category: str
) -> ArticleData:
    title_tag = soup.select_one("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Untitled"

    return ArticleData(
        url=url,
        category=category,
        title=title,
        author=_extract_author(soup),
        published_at=_extract_publish_date(soup),
        summary=_extract_summary(soup),
        content=_extract_content(soup),
        image_url=_extract_hero_image(soup),
        tags=_extract_tags(soup),
    )


def _extract_author(soup: BeautifulSoup) -> str | None:
    author_tag = soup.select_one(
        "[rel='author'], .article__byline a, .wp-block-tc23-author-card-name a"
    )
    if author_tag:
        return author_tag.get_text(strip=True)
    return None


def _extract_publish_date(soup: BeautifulSoup) -> datetime | None:
    time_tag = soup.select_one("time[datetime]")
    if time_tag and time_tag.get("datetime"):
        try:
            return datetime.fromisoformat(str(time_tag["datetime"]))
        except ValueError:
            pass

    meta_tag = soup.select_one('meta[property="article:published_time"]')
    if meta_tag and meta_tag.get("content"):
        try:
            return datetime.fromisoformat(str(meta_tag["content"]))
        except ValueError:
            pass

    return None


def _extract_summary(soup: BeautifulSoup) -> str | None:
    meta = soup.select_one(
        'meta[name="description"], meta[property="og:description"]'
    )
    if meta and meta.get("content"):
        return str(meta["content"]).strip()
    return None


def _extract_content(soup: BeautifulSoup) -> str:
    article_body = soup.select_one(
        ".article-content, .entry-content, article .post-content"
    )
    if not article_body:
        article_body = soup.select_one("article")

    if not article_body:
        return ""

    paragraphs: list[str] = []
    for element in article_body.find_all(["p", "h2", "h3", "blockquote"]):
        if isinstance(element, Tag):
            text = element.get_text(strip=True)
            if text:
                paragraphs.append(text)

    return "\n\n".join(paragraphs)


def _extract_hero_image(soup: BeautifulSoup) -> str | None:
    og_image = soup.select_one('meta[property="og:image"]')
    if og_image and og_image.get("content"):
        return str(og_image["content"])
    return None


def _extract_tags(soup: BeautifulSoup) -> list[str]:
    tags: list[str] = []
    for tag_link in soup.select('a[rel="tag"], .article-tags a'):
        text = tag_link.get_text(strip=True)
        if text:
            tags.append(text)
    return tags
