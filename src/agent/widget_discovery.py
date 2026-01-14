"""Widget discovery module for fetching and displaying available widgets."""

import logging

from registry import WIDGETS

logger = logging.getLogger(__name__)


async def fetch_available_widgets() -> dict:
    """Return locally registered widgets.

    Returns:
        dict: Widget configurations keyed by widget_id
    """
    return WIDGETS


def format_widgets_list(widgets: dict) -> str:
    """Format the widgets catalog for display to the user.

    Args:
        widgets: Widget configurations keyed by widget_id

    Returns:
        Formatted markdown string listing available widgets
    """
    if not widgets:
        return "No widgets available. Make sure the widget backend is running."

    lines = ["**Available Widgets:**\n"]

    for widget_id, config in widgets.items():
        name = config.get("name", widget_id)
        description = config.get("description", "No description")
        widget_type = config.get("type", "table")

        # Get parameter info
        params = config.get("params", [])
        param_names = [p.get("paramName", "?") for p in params]
        param_str = f" (params: {', '.join(param_names)})" if param_names else ""

        lines.append(f"- **{name}** (`{widget_id}`) - _{widget_type}_{param_str}")
        lines.append(f"  {description}")
        lines.append("")

    lines.append("\n_Use `add <widget_id>` or `add <widget_id> <symbol>` to add a widget._")

    return "\n".join(lines)
