import json
import logging

import httpx

from src.config import settings
from src.vianexus.schemas import StockStatsData, VnxQuoteData


class Dataset:
    def __init__(self, namespace: str, dataset: str):
        self.base_url = settings.vianexus_base_url
        self.api_key = settings.vianexus_api_key
        self.namespace = namespace
        self.dataset = dataset

    def make_request(self, symbols: list[str], last: int = 1):
        """Make a request to the Vianexus API to get the data for the dataset for the given symbols"""
        url = f"{self.base_url}/data/{self.namespace}/{self.dataset}/{','.join(symbols)}"
        params = {
            "token": self.api_key,
            "last": last,
        }
        response = httpx.get(url, params=params, timeout=10)
        return response.json()

    def data(self, symbols: list[str], last: int = 1):
        """Get historical data for the dataset for the given symbols

        Args:
            symbols: List of stock symbols
            last: Number of historical records to fetch (default: 30 for ~1 month)
        """
        data = self.make_request(symbols, last=last)
        logging.debug(f"Data: \n{json.dumps(data, indent=4)}")
        return data


class StockStats(Dataset):
    def __init__(self):
        super().__init__("CORE", "STOCK_STATS_US")

    def data(self, symbols: list[str], last: int = 1) -> list[StockStatsData]:
        """Get stock statistics data with validated schema

        Args:
            symbols: List of stock symbols
            last: Number of historical records to fetch (default: 1)

        Returns:
            List of validated StockStatsData objects
        """
        raw_data = super().data(symbols, last=last)
        return [StockStatsData(**item) for item in raw_data]


class VnxQuote(Dataset):
    def __init__(self):
        super().__init__("EDGE", "VNX_QUOTE")

    def data(self, symbols: list[str], last: int = 1) -> list[VnxQuoteData]:
        """Get VNX quote data with validated schema

        Args:
            symbols: List of stock symbols
            last: Number of historical records to fetch (default: 1)

        Returns:
            List of validated VnxQuoteData objects
        """
        raw_data = super().data(symbols, last=last)
        return [VnxQuoteData(**item) for item in raw_data]


stock_stats = StockStats()
vnx_quote = VnxQuote()
