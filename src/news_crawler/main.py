"""Entry point: crawl, translate, store, and schedule the pipeline."""

from __future__ import annotations

import logging
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from news_crawler.core.config import CATEGORIES, settings
from news_crawler.core.database import engine, get_session
from news_crawler.core.exceptions import CrawlerError, NewsCrawlerError
from news_crawler.models.article import Base, TranslatedArticle
from news_crawler.services.crawler import fetch_article_links, scrape_article
from news_crawler.services.repository import get_existing_urls, upsert_article
from news_crawler.services.rss_checker import fetch_rss_urls

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _process_article(url: str, category: str) -> TranslatedArticle:
    """Scrape a single URL and optionally translate it."""
    article_data = scrape_article(url, category)

    if settings.enable_translation:
        from news_crawler.services.translator import translate_article

        return translate_article(article_data)

    return TranslatedArticle(
        url=article_data.url,
        category=article_data.category,
        title_original=article_data.title,
        title_vi="",
        author=article_data.author,
        published_at=article_data.published_at,
        summary_original=article_data.summary,
        summary_vi=None,
        content_original=article_data.content,
        content_vi="",
        image_url=article_data.image_url,
        tags=", ".join(article_data.tags) if article_data.tags else None,
    )


def _save_article(translated: TranslatedArticle) -> bool:
    """Upsert a single article and return True if newly inserted."""
    session = get_session()
    try:
        is_new = upsert_article(session, translated)
        session.commit()
        return is_new
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def run_rss_check() -> None:
    """Quick check: fetch RSS feeds for all categories, crawl only NEW articles."""
    logger.info("=== RSS check started ===")
    total_inserted = 0
    total_failed = 0

    for category, base_url in CATEGORIES.items():
        try:
            rss_urls = fetch_rss_urls(base_url)
        except CrawlerError:
            logger.error("RSS check failed for [%s]", category)
            continue

        session = get_session()
        try:
            existing = get_existing_urls(session, rss_urls)
        finally:
            session.close()

        new_urls = [u for u in rss_urls if u not in existing]

        if not new_urls:
            logger.info("RSS [%s]: no new articles", category)
            continue

        logger.info("RSS [%s]: found %d new article(s)", category, len(new_urls))

        for url in new_urls:
            try:
                translated = _process_article(url, category)
                _save_article(translated)
                total_inserted += 1
            except NewsCrawlerError:
                total_failed += 1
                logger.warning("Skipping article: %s", url)
            except Exception:
                total_failed += 1
                logger.exception("Unexpected error: %s", url)
            time.sleep(1)

    logger.info(
        "=== RSS check finished: %d inserted, %d failed ===",
        total_inserted,
        total_failed,
    )


def run_full_crawl() -> None:
    """Full crawl: scan all listing pages for every category, upsert all articles."""
    logger.info("=== Full crawl started ===")
    total_inserted = 0
    total_updated = 0
    total_failed = 0

    for category, base_url in CATEGORIES.items():
        logger.info("--- Crawling [%s] ---", category)

        try:
            urls = fetch_article_links(base_url)
        except CrawlerError:
            logger.error("Failed to fetch links for [%s], skipping", category)
            continue

        for url in urls:
            try:
                translated = _process_article(url, category)
                is_new = _save_article(translated)
                if is_new:
                    total_inserted += 1
                else:
                    total_updated += 1
            except NewsCrawlerError:
                total_failed += 1
                logger.warning("Skipping article: %s", url)
            except Exception:
                total_failed += 1
                logger.exception("Unexpected error: %s", url)
            time.sleep(1)

    logger.info(
        "=== Full crawl finished: %d inserted, %d updated, %d failed ===",
        total_inserted,
        total_updated,
        total_failed,
    )


def main() -> None:
    """Initialize DB, run once, then schedule RSS checks + full crawls."""
    _setup_logging()
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    logger.info(
        "Categories: %s",
        ", ".join(CATEGORIES.keys()),
    )

    logger.info("Running initial full crawl...")
    run_full_crawl()

    rss_interval = settings.rss_check_interval_minutes
    full_interval = settings.scheduler_interval_hours

    logger.info(
        "Scheduling: RSS check every %d min, full crawl every %d hours",
        rss_interval,
        full_interval,
    )

    scheduler = BlockingScheduler()
    # scheduler.add_job(run_rss_check, "interval", minutes=rss_interval)
    scheduler.add_job(run_full_crawl, "interval", hours=full_interval)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
