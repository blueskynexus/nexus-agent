"""Agent module for nexus-agent SSE streaming and widget handling."""

from src.agent.stream_response import stream_response
from src.agent.widget_context import format_widget_context
from src.agent.widget_discovery import fetch_available_widgets, format_widgets_list

__all__ = [
    "stream_response",
    "format_widget_context",
    "fetch_available_widgets",
    "format_widgets_list",
]
