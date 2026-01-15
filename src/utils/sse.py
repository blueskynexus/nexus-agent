"""SSE utilities for OpenBB streaming responses."""

import logging

from fastapi import Request
from openbb_ai import message_chunk as openbb_message_chunk
from openbb_ai.models import FunctionCallSSE, FunctionCallSSEData

logger = logging.getLogger(__name__)

# In-memory token storage (simple single-token store for now)
stored_token: str | None = None


def sse_message_chunk(content: str):
    """Create a copilotMessageChunk SSE event for streaming text."""
    logger.debug(f"Creating message chunk: {content}")
    return openbb_message_chunk(content).model_dump(exclude_none=True)


def extract_token(request: Request, query_token: str | None) -> str | None:
    """Extract token from query params, headers, or stored value."""
    global stored_token

    # Debug: log what we're receiving
    logger.debug(f"Query params: {dict(request.query_params)}")
    logger.debug(f"Headers: {dict(request.headers)}")

    # Priority: query param > header > stored
    token = query_token

    if not token:
        # Check headers (OpenBB may pass custom params as headers)
        token = request.headers.get("token") or request.headers.get("x-token")

    if token:
        # Store for future requests
        stored_token = token
        logger.info(f"Token received and stored (ends with: ...{token[-8:]})")

    return token or stored_token


def get_extra_widget_data(widget_requests: list) -> dict:
    """Create an SSE event to request data for extra widgets (uploaded files).

    This is similar to get_widget_data but uses the 'get_extra_widget_data' function
    which is used for widgets.extra (uploaded files, artifacts).

    Args:
        widget_requests: List of WidgetRequest objects containing widget and input_arguments

    Returns:
        SSE event dict ready to yield from a streaming response
    """
    data_sources = []
    for widget_request in widget_requests:
        data_sources.append(
            {
                "widget_uuid": str(widget_request.widget.uuid),
                "origin": widget_request.widget.origin,
                "id": widget_request.widget.widget_id,
                "input_args": widget_request.input_arguments,
            }
        )

    return FunctionCallSSE(
        data=FunctionCallSSEData(
            function="get_extra_widget_data",
            input_arguments={"data_sources": data_sources},
        )
    ).model_dump(exclude_none=True)


def add_widget_to_dashboard(
    origin: str,
    widget_id: str,
    input_args: dict,
) -> dict:
    """Create an SSE event to add a new widget to the dashboard.

    This enables the agent to dynamically add pre-configured widgets from
    any connected backend to the user's current dashboard.

    Args:
        origin: Backend name as configured in OpenBB Workspace (e.g., "viaNexus Widgets")
        widget_id: Widget ID from the backend's widgets.json (e.g., "stock_chart")
        input_args: Initial parameter values for the widget (e.g., {"symbol": "AAPL"})

    Returns:
        SSE event dict ready to yield from a streaming response
    """
    return FunctionCallSSE(
        data=FunctionCallSSEData(
            function="add_widget_to_dashboard",
            input_arguments={
                "data_sources": [
                    {
                        "origin": origin,
                        "id": widget_id,
                        "input_args": input_args,
                    }
                ]
            },
        )
    ).model_dump(exclude_none=True)


def update_widget_in_dashboard(
    widget_uuid: str,
    origin: str,
    widget_id: str,
    input_args: dict,
) -> dict:
    """Create an SSE event to update widget parameters in the dashboard.

    This enables the "generative UI" feature where the agent can dynamically
    modify widget parameters (e.g., change ticker symbol from AAPL to MSFT).

    Args:
        widget_uuid: UUID of the widget to update
        origin: Origin/source of the widget (e.g., "viaNexus Test")
        widget_id: Widget ID (e.g., "stock_stats")
        input_args: New parameter values to set (e.g., {"symbol": "MSFT"})

    Returns:
        SSE event dict ready to yield from a streaming response
    """
    return FunctionCallSSE(
        data=FunctionCallSSEData(
            function="update_widget_in_dashboard",
            input_arguments={
                "data_sources": [
                    {
                        "widget_uuid": widget_uuid,
                        "origin": origin,
                        "id": widget_id,
                        "input_args": input_args,
                        "ssm_request": None,
                    }
                ]
            },
        )
    ).model_dump(exclude_none=True)
