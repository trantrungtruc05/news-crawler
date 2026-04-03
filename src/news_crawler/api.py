"""FastAPI application exposing article data via REST endpoints."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from news_crawler.core.database import get_db
from news_crawler.models.article import (
    ArticleDetailResponse,
    ArticleListResponse,
    ArticleSummaryResponse,
    CategoryArticlesResponse,
    CategoryGroup,
    CategoryItemResponse,
    CategoryListResponse,
)
from news_crawler.services.repository import (
    get_all_categories,
    get_article_by_url,
    get_articles_by_category,
    get_articles_grouped_by_category,
)

app = FastAPI(
    title="News Crawler API",
    description="REST API for browsing crawled & translated TechCrunch articles.",
    version="0.1.0",
)


@app.get("/api/articles", response_model=ArticleListResponse)
def list_articles(
    per_category: int = Query(
        default=3,
        ge=1,
        le=20,
        description="Number of latest articles to return per category",
    ),
    db: Session = Depends(get_db),
) -> ArticleListResponse:
    """Return the latest articles grouped by category."""
    grouped = get_articles_grouped_by_category(db, per_category=per_category)

    categories = [
        CategoryGroup(
            category=cat,
            articles=[ArticleSummaryResponse.model_validate(a) for a in articles],
        )
        for cat, articles in grouped.items()
    ]

    return ArticleListResponse(categories=categories)


@app.get("/api/categories", response_model=CategoryListResponse)
def list_categories(
    db: Session = Depends(get_db),
) -> CategoryListResponse:
    """Return all available categories with article counts."""
    rows = get_all_categories(db)
    items = [CategoryItemResponse(**r) for r in rows]
    return CategoryListResponse(categories=items, total=len(items))


@app.get("/api/articles/category/{category}", response_model=CategoryArticlesResponse)
def list_articles_by_category(
    category: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of articles per page",
    ),
    db: Session = Depends(get_db),
) -> CategoryArticlesResponse:
    """Return all articles for a given category with pagination."""
    articles, total = get_articles_by_category(
        db, category=category, page=page, page_size=page_size,
    )
    if total == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No articles found for category '{category}'",
        )
    return CategoryArticlesResponse(
        category=category,
        articles=[ArticleSummaryResponse.model_validate(a) for a in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


@app.get("/api/articles/detail", response_model=ArticleDetailResponse)
def get_article(
    url: str = Query(..., description="The full URL of the article to retrieve"),
    db: Session = Depends(get_db),
) -> ArticleDetailResponse:
    """Return full details for a single article identified by its URL."""
    article = get_article_by_url(db, url)
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleDetailResponse.model_validate(article)
