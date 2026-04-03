"""Custom exceptions for the news crawler application."""

from __future__ import annotations


class NewsCrawlerError(Exception):
    """Base exception for the news crawler."""


class CrawlerError(NewsCrawlerError):
    """Raised when article crawling fails."""


class TranslationError(NewsCrawlerError):
    """Raised when OpenAI translation fails."""


class DatabaseError(NewsCrawlerError):
    """Raised when a database operation fails."""
