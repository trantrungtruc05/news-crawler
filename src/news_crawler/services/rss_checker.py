"""Lightweight RSS feed checker to detect new articles quickly."""

from __future__ import annotations

import logging
from xml.etree import ElementTree

import httpx

from news_crawler.core.config import settings
from news_crawler.core.exceptions import CrawlerError

logger = logging.getLogger(__name__)


def fetch_rss_urls(base_url: str) -> list[str]:
    """Fetch article URLs from an RSS feed derived from the listing URL.

    Args:
        base_url: The category/tag listing URL (feed URL is derived automatically).

    Returns:
        List of article URLs from the RSS feed.

    Raises:
        CrawlerError: If the RSS feed cannot be fetched or parsed.
    """
    rss_url = base_url.rstrip("/") + "/feed/"
    logger.info("Checking RSS feed: %s", rss_url)

    try:
        response = httpx.get(
            rss_url,
            headers={"User-Agent": "NewsCrawler/1.0"},
            timeout=settings.crawl_timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.exception("Failed to fetch RSS feed: %s", rss_url)
        raise CrawlerError(f"Cannot fetch RSS feed: {exc}") from exc

    try:
        root = ElementTree.fromstring(response.text)
    except ElementTree.ParseError as exc:
        logger.exception("Failed to parse RSS XML: %s", rss_url)
        raise CrawlerError(f"Invalid RSS XML: {exc}") from exc

    urls: list[str] = []
    for item in root.iter("item"):
        link = item.find("link")
        if link is not None and link.text:
            urls.append(link.text.strip())

    logger.info("RSS feed returned %d article URLs", len(urls))
    return urls
