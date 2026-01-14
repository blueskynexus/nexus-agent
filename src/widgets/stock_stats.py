"""Stock Statistics Metric Widget.

This widget displays key stock statistics and metrics powered by the Vianexus API.
It shows fundamental and technical indicators including PE ratio, EPS, moving averages,
52-week highs/lows, and volume data.
"""

import logging
from datetime import datetime

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from registry import register_widget
from src.vianexus.dataset import stock_stats, vnx_quote

logger = logging.getLogger(__name__)


@register_widget(
    {
        "name": "Stock Statistics",
        "description": "Key stock statistics and metrics powered by Vianexus",
        "category": "Stock Data",
        "endpoint": "stock_stats",
        "gridData": {"w": 30, "h": 15},
        "type": "metric",
        "params": [
            {
                "paramName": "symbol",
                "value": "AAPL",
                "label": "Stock Symbol",
                "type": "text",
                "description": "Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)",
            },
            {
                "paramName": "metrics_display",
                "value": "all",
                "label": "Metrics to Display",
                "type": "text",
                "description": "Choose which metrics to display",
                "options": [
                    {"label": "All Metrics", "value": "all"},
                    {"label": "Price & Performance", "value": "price_performance"},
                    {"label": "Fundamentals Only", "value": "fundamentals"},
                    {"label": "Technical Only", "value": "technical"},
                ],
            },
        ],
    }
)
def get_stock_stats(symbol: str = "AAPL", metrics_display: str = "all"):
    """Returns stock statistics as metrics for a given symbol.

    Args:
        symbol (str): Stock ticker symbol. Defaults to "AAPL".
        metrics_display (str): Which metrics to display. Options: "all", "price_performance",
                              "fundamentals", "technical". Defaults to "all".

    Returns:
        JSONResponse: Array of metric objects with stock statistics.

    Raises:
        HTTPException: If the API call fails or symbol is invalid.
    """
    try:
        # Fetch data from Vianexus API
        response = stock_stats.data([symbol.upper()])

        # Check if we got valid data
        if not response or len(response) == 0:
            raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")

        # Extract the first (and only) result
        data = response[0]

        # Try to fetch real-time quote data
        quote_data = None
        try:
            quote_response = vnx_quote.data([symbol.upper()])
            if quote_response and len(quote_response) > 0:
                quote_data = quote_response[0]
        except Exception as e:
            logger.warning(f"Could not fetch quote data for {symbol}: {str(e)}")
            # Continue without quote data

        # Build metrics array
        metrics = []

        # Determine which sections to include based on metrics_display parameter
        show_performance = metrics_display in ["all", "price_performance"]
        show_fundamentals = metrics_display in ["all", "fundamentals"]
        show_technical = metrics_display in ["all", "technical"]

        # ============================================================
        # SECTION 1: PRICE & MARKET DATA
        # ============================================================

        # Company name and symbol
        if data.issuer_name:
            company_display = data.issuer_name
            # Add ticker symbol to company name
            if data.symbol:
                company_display = f"{company_display} ({data.symbol})"
            metrics.append({"label": "Company", "value": company_display})

        # Exchange information
        if data.mic:
            # Map common MIC codes to exchange names
            mic_to_exchange = {
                "XNYS": "NYSE",
                "XNAS": "NASDAQ",
                "XASE": "NYSE American",
                "ARCX": "NYSE Arca",
                "BATS": "CBOE BZX",
                "IEXG": "IEX",
            }
            exchange_name = mic_to_exchange.get(data.mic, data.mic)
            metrics.append({"label": "Exchange", "value": f"{data.mic} • {exchange_name}"})

        # Current Price (from VNX_QUOTE if available)
        if quote_data and quote_data.vnx_price:
            current_price = quote_data.vnx_price
            metrics.append(
                {
                    "label": "Current Price",
                    "value": f"${current_price:.2f}",
                    "description": "Real-time price",
                }
            )

            # Market Cap (price * shares outstanding)
            if data.shares_outstanding:
                market_cap = current_price * data.shares_outstanding
                if market_cap >= 1_000_000_000_000:  # Trillion
                    market_cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
                elif market_cap >= 1_000_000_000:  # Billion
                    market_cap_str = f"${market_cap / 1_000_000_000:.2f}B"
                elif market_cap >= 1_000_000:  # Million
                    market_cap_str = f"${market_cap / 1_000_000:.2f}M"
                else:
                    market_cap_str = f"${market_cap:,.0f}"

                metrics.append({"label": "Market Cap", "value": market_cap_str})

        # Day's Range (from VNX_QUOTE if available)
        if quote_data and quote_data.vnx_low_price and quote_data.vnx_high_price:
            day_low = quote_data.vnx_low_price
            day_high = quote_data.vnx_high_price
            if day_low > 0 and day_high > 0:  # Valid range
                metrics.append(
                    {"label": "Day's Range", "value": f"${day_low:.2f} - ${day_high:.2f}"}
                )

        # Bid/Ask (from VNX_QUOTE if available)
        if quote_data and quote_data.vnx_bid_price and quote_data.vnx_ask_price:
            bid = quote_data.vnx_bid_price
            ask = quote_data.vnx_ask_price
            if bid > 0 and ask > 0:  # Valid bid/ask
                metrics.append({"label": "Bid / Ask", "value": f"${bid:.2f} / ${ask:.2f}"})

        # Today's Volume vs Average (from VNX_QUOTE if available)
        if quote_data and quote_data.vnx_volume and data.avg_30_day_volume:
            today_volume = quote_data.vnx_volume
            avg_volume = data.avg_30_day_volume

            # Format today's volume
            if today_volume >= 1_000_000:
                today_str = f"{today_volume / 1_000_000:.2f}M"
            elif today_volume >= 1_000:
                today_str = f"{today_volume / 1_000:.2f}K"
            else:
                today_str = f"{today_volume:,}"

            # Format average volume
            if avg_volume >= 1_000_000:
                avg_str = f"{avg_volume / 1_000_000:.2f}M"
            elif avg_volume >= 1_000:
                avg_str = f"{avg_volume / 1_000:.2f}K"
            else:
                avg_str = f"{avg_volume:,}"

            # Calculate comparison
            if avg_volume > 0:
                volume_ratio = today_volume / avg_volume - 1
                metrics.append(
                    {
                        "label": "Volume (Today vs Avg)",
                        "value": f"{today_str} / {avg_str}",
                        "delta": f"{volume_ratio:.4f}",
                        "description": "Today / 30-day average",
                    }
                )
            else:
                metrics.append({"label": "Volume (Today)", "value": today_str})
        elif data.avg_30_day_volume:
            # Fallback to just showing average volume if no real-time data
            volume = data.avg_30_day_volume
            if volume >= 1_000_000:
                volume_str = f"{volume / 1_000_000:.2f}M"
            elif volume >= 1_000:
                volume_str = f"{volume / 1_000:.2f}K"
            else:
                volume_str = f"{volume:,}"
            metrics.append({"label": "Avg 30-Day Volume", "value": volume_str})

        # ============================================================
        # SECTION 2: PERFORMANCE METRICS
        # ============================================================

        if show_performance:
            # 52-Week High
            if data.week_52_high:
                metrics.append(
                    {
                        "label": "52-Week High",
                        "value": f"${data.week_52_high:.2f}",
                        "description": f"Date: {data.week_52_high_date}",
                    }
                )

            # 52-Week Low
            if data.week_52_low:
                metrics.append(
                    {
                        "label": "52-Week Low",
                        "value": f"${data.week_52_low:.2f}",
                        "description": f"Date: {data.week_52_low_date}",
                    }
                )

            # 52-Week Change
            if data.week_52_change:
                change_pct = data.week_52_change * 100
                metrics.append(
                    {
                        "label": "52-Week Change",
                        "value": f"{change_pct:+.2f}%",
                        "delta": f"{data.week_52_change:.4f}",
                    }
                )

            # YTD Change
            if data.ytd_change:
                ytd_pct = data.ytd_change * 100
                metrics.append(
                    {
                        "label": "YTD Change",
                        "value": f"{ytd_pct:+.2f}%",
                        "delta": f"{data.ytd_change:.4f}",
                    }
                )

        # ============================================================
        # SECTION 3: FUNDAMENTAL METRICS
        # ============================================================

        if show_fundamentals:
            # PE Ratio
            if data.pe_ratio_ttm:
                metrics.append({"label": "P/E Ratio (TTM)", "value": f"{data.pe_ratio_ttm:.2f}"})

            # EPS
            if data.eps_ttm:
                metrics.append({"label": "EPS (TTM)", "value": f"${data.eps_ttm:.2f}"})

            # Beta
            if data.beta:
                metrics.append(
                    {
                        "label": "Beta",
                        "value": f"{data.beta:.2f}",
                        "description": "Volatility measure vs. market",
                    }
                )

        # ============================================================
        # SECTION 4: TECHNICAL INDICATORS
        # ============================================================

        if show_technical:
            # 50-Day Moving Average
            if data.day_50_moving_average:
                metrics.append(
                    {"label": "50-Day MA", "value": f"${data.day_50_moving_average:.2f}"}
                )

            # 200-Day Moving Average
            if data.day_200_moving_average:
                metrics.append(
                    {"label": "200-Day MA", "value": f"${data.day_200_moving_average:.2f}"}
                )

            # Shares Outstanding
            if data.shares_outstanding:
                shares = data.shares_outstanding
                if shares >= 1_000_000_000:
                    shares_str = f"{shares / 1_000_000_000:.2f}B"
                elif shares >= 1_000_000:
                    shares_str = f"{shares / 1_000_000:.2f}M"
                else:
                    shares_str = f"{shares:,}"

                metrics.append({"label": "Shares Outstanding", "value": shares_str})

        # ============================================================
        # DATA FRESHNESS
        # ============================================================

        # Last updated timestamp
        if data.updated:
            # Convert millisecond timestamp to datetime
            updated_ms = data.updated
            updated_dt = datetime.fromtimestamp(updated_ms / 1000)

            # Calculate time ago
            now = datetime.now()
            time_diff = now - updated_dt

            if time_diff.total_seconds() < 60:
                time_ago = "Just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() / 60)
                time_ago = f"{minutes} min ago"
            elif time_diff.total_seconds() < 86400:
                hours = int(time_diff.total_seconds() / 3600)
                time_ago = f"{hours} hr ago" if hours == 1 else f"{hours} hrs ago"
            else:
                days = int(time_diff.total_seconds() / 86400)
                time_ago = f"{days} day ago" if days == 1 else f"{days} days ago"

            metrics.append(
                {
                    "label": "Last Updated",
                    "value": time_ago,
                    "description": updated_dt.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return JSONResponse(content=metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock stats for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching data for symbol {symbol}: {str(e)}"
        )
