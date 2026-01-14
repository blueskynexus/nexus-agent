import json

from openbb_ai import QueryRequest as OpenBBQueryRequest


def format_widget_context(query: OpenBBQueryRequest) -> str | None:
    """Format widget metadata, params, and context data for the LLM.

    Args:
        query: The OpenBBQueryRequest containing widgets and context

    Returns:
        Formatted string for LLM context, or None if no data
    """
    widgets = query.widgets
    context = query.context

    if not widgets and not context:
        return None

    parts = []

    # Format widget metadata with all fields needed for update_widget tool
    if widgets and widgets.primary:
        parts.append("## Dashboard Widgets (Available for Updates)")
        for widget in widgets.primary:
            widget_info = [f"### {widget.name}"]
            widget_info.append(f"- **UUID:** `{widget.uuid}`")
            widget_info.append(f"- **Origin:** `{widget.origin}`")
            widget_info.append(f"- **Widget ID:** `{widget.widget_id}`")
            if widget.description:
                widget_info.append(f"- **Description:** {widget.description}")
            # Extract params - this is where the actual data lives (e.g., watchlist symbols)
            if widget.params:
                params_dict = {}
                param_names = []
                for param in widget.params:
                    param_names.append(param.name)
                    value = (
                        param.current_value if param.current_value is not None else param.default
                    )
                    if value is not None:
                        params_dict[param.name] = value
                if params_dict:
                    widget_info.append(f"- **Current Parameters:** `{json.dumps(params_dict)}`")
                if param_names:
                    widget_info.append(f"- **Updatable Parameters:** {', '.join(param_names)}")
            parts.append("\n".join(widget_info))

    # Also include secondary widgets if present
    if widgets and widgets.secondary:
        for widget in widgets.secondary:
            widget_info = [f"Dashboard Widget: {widget.name}"]
            if widget.params:
                params_dict = {}
                for param in widget.params:
                    value = (
                        param.current_value if param.current_value is not None else param.default
                    )
                    if value is not None:
                        params_dict[param.name] = value
                if params_dict:
                    widget_info.append(f"Parameters: {json.dumps(params_dict)}")
            parts.append("\n".join(widget_info))

    # Also include context if present (from get_widget_data callback)
    if context:
        context_str = json.dumps(context, indent=2, default=str)
        parts.append(f"Widget Data:\n{context_str}")

    return "\n\n".join(parts) if parts else None
