"""Financial news widget displaying articles from viaNexus."""

from datetime import datetime

from fastapi import HTTPException

from registry import register_widget
from src.vianexus.news import news


def epoch_ms_to_iso(epoch_ms: int) -> str:
    """Convert epoch milliseconds to ISO 8601 string."""
    return datetime.fromtimestamp(epoch_ms / 1000).isoformat()


def generate_excerpt(summary: str | None, max_length: int = 200) -> str:
    """Generate excerpt from summary.

    Args:
        summary: Full summary text.
        max_length: Maximum length of excerpt.

    Returns:
        Truncated excerpt with "..." if needed.
    """
    if not summary:
        return ""
    if len(summary) <= max_length:
        return summary
    return summary[:max_length].rsplit(" ", 1)[0] + "..."


def format_body(summary: str | None, qm_url: str | None) -> str:
    """Format body with summary and link to original article.

    Args:
        summary: Full summary text.
        qm_url: URL to the original article.

    Returns:
        Formatted body with markdown link to original article.
    """
    body = summary or ""
    if qm_url:
        body += f"\n\n[Read full article]({qm_url})"
    return body


@register_widget(
    {
        "name": "Financial News",
        "description": "Latest financial news powered by viaNexus",
        "category": "News",
        "type": "newsfeed",
        "endpoint": "vianexus_news",
        "gridData": {"w": 40, "h": 20},
        "refetchInterval": 60000,
        "source": "viaNexus",
        "params": [
            {
                "paramName": "symbol",
                "value": "AAPL",
                "label": "Stock Symbol",
                "type": "text",
                "description": "Filter news by stock symbol (e.g., AAPL, MSFT, GOOGL).",
            },
            {
                "paramName": "limit",
                "value": "10",
                "label": "Number of Articles",
                "type": "number",
                "description": "Maximum number of articles to display",
            },
        ],
    }
)
def get_news(symbol: str = "AAPL", limit: int = 10):
    """Fetch and return financial news articles.

    Args:
        symbol: Optional stock symbol to filter news (e.g., "AAPL").
        limit: Maximum number of articles to display.

    Returns:
        List of articles in OpenBB newsfeed format.

    Raises:
        HTTPException: If the API request fails.
    """
    try:
        # Fetch news from API (pass None if symbol is empty)
        articles = news.fetch(symbol=symbol if symbol else None, limit=limit)

        # Transform to OpenBB newsfeed format
        result = []
        for article in articles:
            result.append(
                {
                    "title": article.headline,
                    "date": epoch_ms_to_iso(article.datetime),
                    "author": article.source or article.provider,
                    "excerpt": generate_excerpt(article.summary),
                    "body": format_body(article.summary, article.qm_url),
                }
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch news: {str(e)}",
        )
