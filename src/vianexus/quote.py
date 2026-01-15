"""News data fetcher for CORE/NEWS dataset."""

import logging

import httpx

from src.config import settings
from src.vianexus.schemas import QuoteData

logger = logging.getLogger(__name__)


class Quote:
    """Fetch quote data from CORE/QUOTE dataset."""

    def __init__(self):
        self.base_url = settings.vianexus_base_url
        self.api_key = settings.vianexus_api_key
        self.namespace = "CORE"
        self.dataset = "QUOTE"

    def fetch(self, symbols: list[str], limit: int = 10) -> list[QuoteData]:
        """Fetch quote data from the API.

        Args:
            symbols: List of stock symbols to fetch quote data for.
            limit: Maximum number of quote data to fetch.
        """
        # Build URL based on whether symbol is provided
        url = f"{self.base_url}/data/{self.namespace}/{self.dataset}/{','.join(symbols)}"

        params = {
            "token": self.api_key,
            "last": limit,
        }

        logger.debug(f"Fetching quote data from {url} with params: {params}")

        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()

        raw_data = response.json()
        logger.debug(f"Received {len(raw_data)} quote data")

        return [QuoteData(**item) for item in raw_data]


quote = Quote()
