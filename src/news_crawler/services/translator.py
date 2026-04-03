"""Translate article content to Vietnamese using OpenAI API."""

from __future__ import annotations

import logging

from openai import OpenAI

from news_crawler.core.config import settings
from news_crawler.core.exceptions import TranslationError
from news_crawler.models.article import ArticleData, TranslatedArticle

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a professional translator specializing in technology news. "
    "Translate the following English text to Vietnamese. "
    "Keep technical terms, brand names, and proper nouns in English. "
    "Maintain the original formatting and paragraph structure. "
    "Produce natural, fluent Vietnamese suitable for a news publication."
)


def translate_article(article: ArticleData) -> TranslatedArticle:
    """Translate all text fields of an article to Vietnamese.

    Args:
        article: The scraped article with English text.

    Returns:
        A fully translated article ready for database upsert.

    Raises:
        TranslationError: If the OpenAI API call fails.
    """
    logger.info("Translating article: %s", article.title)

    title_vi = _translate_text(article.title)
    summary_vi = _translate_text(article.summary) if article.summary else None
    content_vi = _translate_text(article.content)

    return TranslatedArticle(
        url=article.url,
        category=article.category,
        title_original=article.title,
        title_vi=title_vi,
        author=article.author,
        published_at=article.published_at,
        summary_original=article.summary,
        summary_vi=summary_vi,
        content_original=article.content,
        content_vi=content_vi,
        image_url=article.image_url,
        tags=", ".join(article.tags) if article.tags else None,
    )


def _translate_text(text: str) -> str:
    if not text.strip():
        return text

    client = OpenAI(api_key=settings.openai_api_key)

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
        )
        translated = response.choices[0].message.content
        if not translated:
            raise TranslationError("OpenAI returned empty translation")
        return translated.strip()
    except TranslationError:
        raise
    except Exception as exc:
        logger.exception("OpenAI translation failed")
        raise TranslationError(f"Translation failed: {exc}") from exc
