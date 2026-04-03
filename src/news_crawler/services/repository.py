"""Database operations for articles (upsert / query)."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from news_crawler.core.exceptions import DatabaseError
from news_crawler.models.article import Article, TranslatedArticle

logger = logging.getLogger(__name__)


def get_existing_urls(session: Session, urls: list[str]) -> set[str]:
    """Return the subset of URLs that already exist in the database.

    Args:
        session: Active SQLAlchemy session.
        urls: List of article URLs to check.

    Returns:
        Set of URLs that are already stored.
    """
    if not urls:
        return set()

    rows = session.query(Article.url).filter(Article.url.in_(urls)).all()
    return {row[0] for row in rows}


def upsert_article(session: Session, data: TranslatedArticle) -> bool:
    """Insert a new article or update an existing one.

    The article URL is used as the unique key. If the article already
    exists, all fields are updated in place.

    Args:
        session: Active SQLAlchemy session.
        data: Translated article data to persist.

    Returns:
        True if a new row was inserted, False if an existing row was updated.

    Raises:
        DatabaseError: If the upsert fails.
    """
    try:
        existing: Article | None = session.get(Article, data.url)

        if existing:
            existing.category = data.category
            existing.title_original = data.title_original
            existing.title_vi = data.title_vi
            existing.author = data.author
            existing.published_at = data.published_at
            existing.summary_original = data.summary_original
            existing.summary_vi = data.summary_vi
            existing.content_original = data.content_original
            existing.content_vi = data.content_vi
            existing.image_url = data.image_url
            existing.tags = data.tags
            logger.info("Updated [%s]: %s", data.category, data.url)
            return False

        article = Article(
            url=data.url,
            category=data.category,
            title_original=data.title_original,
            title_vi=data.title_vi,
            author=data.author,
            published_at=data.published_at,
            summary_original=data.summary_original,
            summary_vi=data.summary_vi,
            content_original=data.content_original,
            content_vi=data.content_vi,
            image_url=data.image_url,
            tags=data.tags,
        )
        session.add(article)
        logger.info("Inserted [%s]: %s", data.category, data.url)
        return True

    except Exception as exc:
        logger.exception("Upsert failed for %s", data.url)
        raise DatabaseError(f"Upsert failed for {data.url}: {exc}") from exc
