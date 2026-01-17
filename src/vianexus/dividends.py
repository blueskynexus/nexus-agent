"""News data fetcher for CORE/ADVANCED_DIVIDENDS dataset."""

import logging

import httpx

from src.config import settings
from src.vianexus.schemas import AdvancedDividends as AdvancedDividendsSchema

logger = logging.getLogger(__name__)


class AdvancedDividends:
    """Fetch advanced dividends data from CORE/ADVANCED_DIVIDENDS dataset."""

    def __init__(self):
        self.base_url = settings.vianexus_base_url
        self.api_key = settings.vianexus_api_key
        self.namespace = "CORE"
        self.dataset = "ADVANCED_DIVIDENDS"

    def fetch(self, symbols: list[str] | None = None, limit: int = 1, from_date: str = "2024-01-01") -> list[AdvancedDividendsSchema]:
        """Fetch advanced dividends data from the API.

        Args:
            symbols: A list of stock symbols to fetch advanced dividends data for.
            limit: Maximum number of advanced dividends data to fetch.
        """
        # Build URL based on whether symbol is provided
        url = f"{self.base_url}/data/{self.namespace}/{self.dataset}"
        if symbols:
            url += f"/{','.join(symbols)}"

        params = {
            "token": self.api_key,
            "last": limit,
            "from": from_date,
        }

        logger.debug(f"Fetching advanced dividends data from {url} with params: {params}")

        response = httpx.get(url, params=params, timeout=10)
        response.raise_for_status()

        raw_data = response.json()
        logger.debug(f"Received {len(raw_data)} advanced dividends data")

        return [AdvancedDividendsSchema(**item) for item in raw_data]


advanced_dividends = AdvancedDividends()
