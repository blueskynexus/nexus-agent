"""News data fetcher for CORE/NEWS dataset."""

import logging

import httpx

from src.config import settings
from src.vianexus.schemas import NewsArticle

logger = logging.getLogger(__name__)


class News:
    """Fetch news from CORE/NEWS dataset."""

    def __init__(self):
        self.base_url = settings.vianexus_base_url
        self.api_key = settings.vianexus_api_key
        self.namespace = "CORE"
        self.dataset = "NEWS"

    def fetch(self, symbol: str | None = None, limit: int = 10) -> list[NewsArticle]:
        """Fetch news articles from the API.

        Args:
            symbol: Optional stock symbol to filter news (e.g., "AAPL").
                   If None, returns market-wide news.
            limit: Maximum number of articles to fetch.

        Returns:
            List of validated NewsArticle objects.
        """
        # Build URL based on whether symbol is provided
        if symbol:
            url = f"{self.base_url}/data/{self.namespace}/{self.dataset}/{symbol.upper()}"
        else:
            url = f"{self.base_url}/data/{self.namespace}/{self.dataset}"

        params = {
            "token": self.api_key,
            "last": limit,
        }

        logger.debug(f"Fetching news from {url} with params: {params}")

        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()

        raw_data = response.json()
        logger.debug(f"Received {len(raw_data)} news articles")

        return [NewsArticle(**item) for item in raw_data]


news = News()
