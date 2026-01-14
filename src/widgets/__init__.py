"""OpenBB Workspace widgets.

This package contains all widget implementations for the OpenBB Workspace backend.
Each widget module defines its configuration and endpoint logic using the
@register_widget decorator pattern.

To add a new widget:
1. Create a new module in this directory (e.g., my_widget.py)
2. Import the app and register_widget decorator
3. Define your widget using @register_widget decorator
4. Import your widget in this __init__.py to ensure it's registered

Example:
    from .my_widget import my_endpoint
"""

# Import all widgets to ensure they are registered
from .news import get_news
from .stock_chart import get_stock_chart
from .stock_stats import get_stock_stats

__all__ = ["get_stock_stats", "get_stock_chart", "get_news"]
