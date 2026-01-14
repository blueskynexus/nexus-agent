"""Stock Price Chart Widget.

This widget displays historical stock price data as an interactive Plotly chart.
It shows price trends over a 1-month period with customizable metrics (future).
"""

import json
import logging

import plotly.graph_objects as go
from fastapi import HTTPException

from registry import register_widget
from src.utils.plotly_config import base_layout
from src.vianexus.dataset import stock_stats

logger = logging.getLogger(__name__)


@register_widget(
    {
        "name": "Moving Averages Chart",
        "description": "Historical moving averages chart for a given stock symbol (1 month)",
        "category": "Stock Data",
        "endpoint": "moving_average_crossover",
        "gridData": {"w": 40, "h": 14},
        "type": "chart",
        "raw": True,  # Enable raw data access for AI
        "params": [
            {
                "paramName": "symbol",
                "value": "AAPL",
                "label": "Stock Symbol",
                "type": "text",
                "description": "Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)",
            }
        ],
    }
)
def get_stock_chart(symbol: str = "AAPL"):
    """Returns historical stock price chart for a given symbol.

    Args:
        symbol (str): Stock ticker symbol. Defaults to "AAPL".

    Returns:
        dict: Plotly figure JSON with historical price data.

    Raises:
        HTTPException: If the API call fails or symbol is invalid.
    """
    try:
        response = stock_stats.data([symbol.upper()], last=30)
        if not response or len(response) == 0:
            raise HTTPException(
                status_code=404, detail=f"No historical data found for symbol: {symbol}"
            )

        # Extract dates and moving averages from the response
        dates = []
        ma_50 = []
        ma_200 = []

        for record in response:
            dates.append(record.date)
            ma_50.append(record.day_50_moving_average)
            ma_200.append(record.day_200_moving_average)

        if len(dates) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient historical data for symbol: {symbol}",
            )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ma_50,
                mode="lines+markers",
                name="50-Day MA",
                line={"color": "#00B140", "width": 2},
                marker={"size": 4},
                hovertemplate="<b>%{x}</b><br>50-Day MA: $%{y:.2f}<extra></extra>",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=ma_200,
                mode="lines+markers",
                name="200-Day MA",
                line={"color": "#FF8000", "width": 2},
                marker={"size": 4},
                hovertemplate="<b>%{x}</b><br>200-Day MA: $%{y:.2f}<extra></extra>",
            )
        )

        # Apply the dark theme layout
        layout = base_layout(x_title="Date", y_title="Price (USD)", y_format="$,.2f")
        layout["title"] = f"{symbol.upper()} - Moving Averages (1 Month)"
        layout["showlegend"] = True  # Show legend for multiple series

        fig.update_layout(layout)

        return json.loads(fig.to_json())  # type: ignore

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock chart for {symbol}: {str(e)}")

        raise HTTPException(
            status_code=500, detail=f"Error fetching chart data for symbol {symbol}: {str(e)}"
        )
