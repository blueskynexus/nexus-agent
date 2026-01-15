"""Editable table widget displaying a list of stocks and their quantities."""

from registry import register_widget
from src.vianexus.quote import quote


@register_widget(
    {
        "name": "Table Widget",
        "description": "A table widget from an API endpoint",
        "type": "table",
        "endpoint": "table_widget",
        "refetchInterval": 10_000,
        "gridData": {"w": 50, "h": 10},
        "raw": True,
        "params": [
            {
                "paramName": "symbols",
                "label": "Stock Symbols",
                "type": "text",
                "multiSelect": True,
                "value": "AAPL,NVDA,MSFT",
            }
        ],
        "data": {
            "table": {
                "columnsDefs": [
                    {
                        "field": "symbol",
                        "headerName": "Symbol",
                        "pinned": "left",
                        "width": 100,
                    },
                    {
                        "field": "price",
                        "headerName": "Price",
                        "width": 100,
                    },
                    {
                        "field": "change",
                        "headerName": "Change",
                        "renderFn": "greenRed",
                        "width": 120,
                        "minWidth": 70,
                    },
                    {
                        "field": "percent_change",
                        "headerName": "% Change",
                        "formatterFn": "percent",
                        "renderFn": "greenRed",
                        "width": 130,
                        "minWidth": 70,
                    },
                    {
                        "field": "prev_close",
                        "headerName": "Prev Close",
                    },
                    {
                        "field": "open",
                        "headerName": "Open",
                        "hide": True,  # Open price is returning null from API
                    },
                    {
                        "field": "high",
                        "headerName": "High",
                    },
                    {
                        "field": "low",
                        "headerName": "Low",
                    },
                    {
                        "field": "volume",
                        "headerName": "Volume",
                        "formatterFn": "int",
                    },
                    {
                        "field": "market_cap",
                        "headerName": "Market Cap",
                        "formatterFn": "int",
                    },
                ]
            }
        },
    }
)
def table_widget(symbols: str = "NVDA,MSFT,AAPL,ORCL,PCG,QQQ"):
    """Returns a table of stock holdings with Symbol, Price, Change, Change %, and Prev Close columns"""
    symbols = symbols.split(",")
    data = quote.fetch(symbols)
    return [
        {
            "symbol": item.symbol,
            "price": item.price,
            "change": item.change,
            "percent_change": item.percent_change,
            "prev_close": item.prev_close,
            "open": item.open,
            "high": item.high,
            "low": item.low,
            "volume": item.volume,
            "market_cap": item.market_cap,
        }
        for item in data
    ]
