"""Editable table widget displaying a list of stocks and their dividends."""

from registry import register_widget
from src.vianexus.dividends import advanced_dividends


@register_widget(
    {
        "name": "Dividends Table",
        "description": "A table widget displaying a list of dividends for a given stock symbol",
        "type": "table",
        "endpoint": "dividends_table",
        "refetchInterval": 60_000,
        "gridData": {"w": 25, "h": 20},
        "raw": True,
        "params": [
            {
                "paramName": "symbols",
                "label": "Stock Symbols",
                "type": "text",
                "value": "AAPL,MSFT,GOOGL",
                "description": "Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)",
            },
            {
                "paramName": "limit",
                "label": "Limit",
                "type": "number",
                "value": 100,
                "description": "Enter the number of dividends to display",
            },
            {
                "paramName": "from_date",
                "label": "From Date",
                "type": "date",
                "value": "2024-01-01",
                "description": "Returns data on or after the given from date. Format YYYY-MM-DD",
            }
        ],
        "data": {
            "table": {
                "columnsDefs": [
                    {
                        "field": "symbol",
                        "headerName": "Symbol",
                        "width": 100,
                    },
                    {
                        "field": "ex_date",
                        "headerName": "Ex-Date",
                        "width": 100,
                    },
                    {
                        "field": "payment_date",
                        "headerName": "Payment Date",
                        "width": 100,
                    },
                    {
                        "field": "record_date",
                        "headerName": "Record Date",
                        "width": 100,
                    },
                    {
                        "field": "amount",
                        "headerName": "Amount",
                        "width": 100,
                    },
                    {
                        "field": "announced_date",
                        "headerName": "Announced Date",
                        "width": 100,
                    },
                ]
            }
        },
    }
)
def dividends_table(symbols: str | None = None, limit: int = 10, from_date: str = "2024-01-01"):
    """Returns a table of dividends for a given stock symbols"""
    data = advanced_dividends.fetch(symbols=symbols.split(",") if symbols else None, limit=limit, from_date=from_date)
    return [
        {
            "symbol": item.symbol,
            "ex_date": item.ex_date,
            "payment_date": item.payment_date,
            "record_date": item.record_date,
            "amount": item.amount,
            "announced_date": item.announce_date,
        }
        for item in data
    ]
