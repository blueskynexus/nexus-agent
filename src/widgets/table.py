"""Editable table widget displaying a list of stocks and their quantities."""

from registry import register_widget

from src.vianexus.quote import quote

@register_widget({
    "name": "Table Widget",
    "description": "A table widget from an API endpoint",
    "type": "table",
    "endpoint": "table_widget",
    "refetchInterval": 60000,
    "gridData": {"w": 20, "h": 10},
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
                },
                {
                    "field": "price",
                    "headerName": "Price",
                },
                {
                    "field": "change",
                    "headerName": "Change",
                },
                {
                    "field": "percent_change",
                    "headerName": "% Change",
                    "formatterFn": "percent",
                },
                {
                    "field": "prev_close",
                    "headerName": "Prev Close",
                },
            ]
        }
    }
})
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
        }
        for item in data
    ]
