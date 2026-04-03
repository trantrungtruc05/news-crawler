"""Convenience entry-point to start the API server via ``news-api``."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run(
        "news_crawler.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
