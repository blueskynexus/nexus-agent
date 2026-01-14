"""Widget registration system for OpenBB Workspace.

This module provides a decorator-based widget registration pattern that
automatically registers widget configurations with their endpoint implementations.
"""

import asyncio
from functools import wraps

# Global dictionary to store registered widgets
WIDGETS = {}


def register_widget(widget_config):
    """
    Decorator that registers a widget configuration in the WIDGETS dictionary.

    This decorator allows you to define both the widget configuration (UI/UX)
    and the endpoint implementation in a single location, maintaining a single
    source of truth for widget definitions.

    Args:
        widget_config (dict): The widget configuration to add to the WIDGETS
            dictionary. Should include:
            - name (str): Display name of the widget
            - description (str): Widget description
            - category (str): Category for organization
            - type (str): Widget type (metric, table, chart, etc.)
            - endpoint (str): API endpoint name
            - gridData (dict): Layout size {"w": width, "h": height}
            - params (list, optional): Parameter definitions

    Returns:
        function: The decorated function.

    Example:
        @register_widget({
            "name": "My Widget",
            "description": "A sample widget",
            "category": "Examples",
            "type": "metric",
            "endpoint": "my_endpoint",
            "gridData": {"w": 12, "h": 8}
        })
        @app.get("/my_endpoint")
        def my_endpoint():
            return [{"label": "Test", "value": "123"}]
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Call the original function
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Call the original function
            return func(*args, **kwargs)

        # Extract the endpoint from the widget_config
        endpoint = widget_config.get("endpoint")
        if endpoint:
            # Add a widgetId field to the widget_config if not already present
            if "widgetId" not in widget_config:
                widget_config["widgetId"] = endpoint

            # Use widgetId as the key to allow multiple widgets per endpoint
            widget_id = widget_config["widgetId"]
            WIDGETS[widget_id] = widget_config

        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
