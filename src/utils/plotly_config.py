"""Plotly configuration for dark theme charts."""

import plotly.graph_objects as go


def get_dark_template():
    """Returns a Plotly template configured for dark theme."""
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={"color": "#ffffff"},
            xaxis={
                "showgrid": False,
                "color": "#ffffff",
                "linecolor": "rgba(128, 128, 128, 0.2)",
            },
            yaxis={
                "showgrid": True,
                "gridcolor": "rgba(128, 128, 128, 0.2)",
                "color": "#ffffff",
                "linecolor": "rgba(128, 128, 128, 0.2)",
            },
            hovermode="x unified",
            hoverlabel={
                "bgcolor": "white",
                "font_color": "black",
            },
        )
    )


def base_layout(x_title=None, y_title=None, y_format=".2f"):
    """Create a base layout for charts with dark theme.

    Args:
        x_title: X-axis title (optional, hidden for date axes)
        y_title: Y-axis title (optional)
        y_format: Y-axis tick format (default: ".2f")

    Returns:
        dict: Plotly layout configuration
    """
    # Hide x-axis title for date/time axes
    if x_title and x_title.lower() in ["date", "time", "timestamp", "datetime"]:
        x_title = None

    return {
        "template": get_dark_template(),
        "xaxis": {"title": x_title, "showgrid": False},
        "yaxis": {"title": y_title, "tickformat": y_format},
        "margin": {"b": 40, "l": 80, "r": 20, "t": 40},
        "hovermode": "x unified",
    }
