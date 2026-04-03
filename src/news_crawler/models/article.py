"""SQLAlchemy model and Pydantic schemas for articles."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class Article(Base):
    """Stores a crawled and translated TechCrunch article."""

    __tablename__ = "articles"

    url = Column(String(2048), primary_key=True)
    category = Column(String(128), nullable=False, index=True)
    title_original = Column(String(1024), nullable=False)
    title_vi = Column(String(1024), nullable=True)
    author = Column(String(256), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    summary_original = Column(Text, nullable=True)
    summary_vi = Column(Text, nullable=True)
    content_original = Column(Text, nullable=False)
    content_vi = Column(Text, nullable=True)
    image_url = Column(String(2048), nullable=True)
    tags = Column(String(1024), nullable=True)
    crawled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Article category={self.category!r} url={self.url!r}>"


class ArticleData(BaseModel):
    """Pydantic schema for a scraped article before translation."""

    url: str
    category: str
    title: str
    author: str | None = None
    published_at: datetime | None = None
    summary: str | None = None
    content: str
    image_url: str | None = None
    tags: list[str] = []


class TranslatedArticle(BaseModel):
    """Pydantic schema for a fully translated article ready for DB upsert."""

    url: str
    category: str
    title_original: str
    title_vi: str
    author: str | None = None
    published_at: datetime | None = None
    summary_original: str | None = None
    summary_vi: str | None = None
    content_original: str
    content_vi: str
    image_url: str | None = None
    tags: str | None = None


# ---------------------------------------------------------------------------
# API response schemas
# ---------------------------------------------------------------------------


class ArticleSummaryResponse(BaseModel):
    """Lightweight article representation for listing endpoints."""

    model_config = {"from_attributes": True}

    url: str
    category: str
    title_original: str
    title_vi: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    summary_vi: str | None = None
    summary_original: str | None = None
    image_url: str | None = None
    tags: str | None = None


class CategoryGroup(BaseModel):
    """A single category with its latest articles."""

    category: str
    articles: list[ArticleSummaryResponse]


class ArticleListResponse(BaseModel):
    """Top-level response for the grouped article listing."""

    categories: list[CategoryGroup]


class CategoryArticlesResponse(BaseModel):
    """Paginated list of articles for a single category."""

    category: str
    articles: list[ArticleSummaryResponse]
    total: int
    page: int
    page_size: int


class CategoryItemResponse(BaseModel):
    """A single category with its article count."""

    name: str
    article_count: int


class CategoryListResponse(BaseModel):
    """Response for the categories listing endpoint."""

    categories: list[CategoryItemResponse]
    total: int


class ArticleDetailResponse(BaseModel):
    """Full article detail including content."""

    model_config = {"from_attributes": True}

    url: str
    category: str
    title_original: str
    title_vi: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    summary_original: str | None = None
    summary_vi: str | None = None
    content_original: str
    content_vi: str | None = None
    image_url: str | None = None
    tags: str | None = None
    crawled_at: datetime
    updated_at: datetime
