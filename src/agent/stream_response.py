import logging
from datetime import datetime
from typing import AsyncGenerator

import httpx
from openbb_ai import QueryRequest as OpenBBQueryRequest
from openbb_ai import WidgetRequest, citations, cite, get_widget_data
from openbb_ai import chart as openbb_chart
from openbb_ai import table as openbb_table

from src.agent.widget_discovery import fetch_available_widgets, format_widgets_list
from src.config import FINANCIAL_AGENT_URL
from src.utils.sse import add_widget_to_dashboard, sse_message_chunk, update_widget_in_dashboard

logger = logging.getLogger(__name__)


def format_timestamp_if_needed(value):
    """Convert Unix timestamps to readable date strings."""
    if not isinstance(value, (int, float)):
        return value

    # Heuristic: Unix timestamps in milliseconds are typically 13 digits (e.g., 1767964317916)
    # Unix timestamps in seconds are typically 10 digits (e.g., 1767964317)
    # Values before year 2000 (946684800000 ms) or after 2100 are likely not timestamps
    if 946684800000 <= value <= 4102444800000:  # ms range: 2000-2100
        return datetime.fromtimestamp(value / 1000).strftime("%Y-%m-%d")
    elif 946684800 <= value <= 4102444800:  # seconds range: 2000-2100
        return datetime.fromtimestamp(value).strftime("%Y-%m-%d")

    return value


async def stream_response(
    query: OpenBBQueryRequest, token: str, session_id: str | None, session_store: dict[str, str]
) -> AsyncGenerator[dict, None]:
    """Stream response from financial agent as SSE events."""

    # Extract the latest user message
    user_messages = [m for m in query.messages if m.role == "human"]
    if not user_messages:
        yield sse_message_chunk("No message provided.")
        return

    latest_message = user_messages[-1].content
    msg_lower = latest_message.strip().lower()

    # Handle "list widgets" command
    if msg_lower in ("list widgets", "widgets", "show widgets", "available widgets"):
        logger.info("Fetching available widgets from backend")
        widgets = await fetch_available_widgets()
        formatted = format_widgets_list(widgets)
        yield sse_message_chunk(formatted)
        return

    # Phase 1: Check if we need to retrieve widget data first
    # When last message is "human" and widgets exist, tell OpenBB to fetch widget data
    last_message = query.messages[-1]
    if last_message.role == "human" and query.widgets and query.widgets.primary:
        logger.info("Phase 1: Requesting widget data retrieval")
        widget_requests: list[WidgetRequest] = []
        for widget in query.widgets.primary:
            widget_requests.append(
                WidgetRequest(
                    widget=widget,
                    input_arguments={param.name: param.current_value for param in widget.params},
                )
            )
        yield get_widget_data(widget_requests).model_dump()
        return

    # Phase 2: Extract widget data from tool messages and build citations
    context_str = ""
    citations_list = []

    has_widget_data = False
    for index, message in enumerate(query.messages):
        if message.role == "tool" and index == len(query.messages) - 1:
            logger.info("Phase 2: Processing tool message with widget data")
            # Build context from tool message data
            context_str = "Use the following data to answer the question:\n\n"
            for result in message.data:
                # Skip results that don't have items (e.g., ClientCommandResult from widget updates)
                if not hasattr(result, "items"):
                    continue
                for item in result.items:
                    context_str += f"{item.content}\n---\n"
                    has_widget_data = True

            # If this is a callback from add_widget/update_widget (no actual data), return silently
            # The LLM already provided a response, so we don't need to yield anything
            if not has_widget_data:
                logger.info(
                    "Tool callback with no widget data - likely add/update widget callback, returning silently"
                )
                return

            # Build citations from widget data
            if query.widgets and query.widgets.primary:
                for widget_data_request in message.input_arguments.get("data_sources", []):
                    filtered_widgets = list(
                        filter(
                            lambda w: str(w.uuid) == widget_data_request["widget_uuid"],
                            query.widgets.primary,
                        )
                    )
                    if filtered_widgets:
                        citations_list.append(
                            cite(
                                widget=filtered_widgets[0],
                                input_arguments=widget_data_request.get("input_args", {}),
                                extra_details=widget_data_request.get("input_args", {}),
                            )
                        )

    # Add widget metadata so LLM knows UUIDs for update_widget tool
    if query.widgets and query.widgets.primary:
        widget_metadata = "\n\n## Available Widgets for Updates\n"
        for widget in query.widgets.primary:
            widget_metadata += f"\n### {widget.name}\n"
            widget_metadata += f"- UUID: `{widget.uuid}`\n"
            widget_metadata += f"- Origin: `{widget.origin}`\n"
            widget_metadata += f"- Widget ID: `{widget.widget_id}`\n"
            if widget.params:
                params = {p.name: p.current_value for p in widget.params if p.current_value}
                widget_metadata += f"- Current Parameters: `{params}`\n"
        context_str = widget_metadata + "\n" + context_str

    # Build request to financial agent with OpenBB client context
    request_body = {
        "message": latest_message,
        "client_context": {
            "type": "openbb",
            "capabilities": ["charts", "tables", "widgets"],
        },
    }

    # Add widget context to request body if present (from Phase 2 tool message)
    if context_str:
        logger.info(f"Widget context extracted: {context_str[:200]}...")
        request_body["widget_context"] = context_str

    # Build URL with query params
    url = f"{FINANCIAL_AGENT_URL}/chat"
    params = {"token": token}
    if session_id:
        params["session_id"] = session_id

    try:
        async with httpx.AsyncClient(
            timeout=300.0
        ) as client:  # 5 min timeout for complex LLM requests
            response = await client.post(url, params=params, json=request_body)
            response.raise_for_status()

            result = response.json()
            agent_response = result.get("response", "")
            new_session_id = result.get("session_id", session_id)
            artifacts = result.get("artifacts", [])

            # Stream the text response in chunks for better UX
            chunk_size = 100
            for i in range(0, len(agent_response), chunk_size):
                chunk = agent_response[i : i + chunk_size]
                yield sse_message_chunk(chunk)

            # Yield SSE events for any captured artifacts (charts, tables)
            for artifact in artifacts:
                artifact_type = artifact.get("artifact_type")
                logger.info(f"Processing artifact: {artifact_type}")

                if artifact_type == "chart":
                    x_key = artifact.get("x_key", "x")
                    y_keys = artifact.get("y_keys", ["y"])
                    raw_data = artifact.get("data", [])

                    # Filter data to only include xKey and yKey fields
                    # This works around OpenBB dashboard not respecting chart_params.yKey
                    keys_to_keep = {x_key} | set(y_keys)
                    filtered_data = []
                    for row in raw_data:
                        filtered_row = {k: v for k, v in row.items() if k in keys_to_keep}
                        # Convert timestamp to readable date if x_key looks like a timestamp
                        if x_key in filtered_row:
                            filtered_row[x_key] = format_timestamp_if_needed(filtered_row[x_key])
                        filtered_data.append(filtered_row)

                    yield openbb_chart(
                        type=artifact.get("chart_type", "line"),
                        data=filtered_data,
                        x_key=x_key,
                        y_keys=y_keys,
                        name=artifact.get("name", "Chart"),
                        description=artifact.get("description", ""),
                    ).model_dump()
                elif artifact_type == "table":
                    yield openbb_table(
                        data=artifact.get("data", []),
                        name=artifact.get("name", "Table"),
                        description=artifact.get("description", ""),
                    ).model_dump()
                elif artifact_type == "widget_update":
                    widget_uuid = artifact.get("widget_uuid")
                    input_args = artifact.get("input_args", {})

                    if not widget_uuid:
                        logger.error("widget_update artifact missing widget_uuid")
                        continue

                    # Look up the widget from query.widgets.primary to get origin and widget_id
                    target_widget = None
                    if query.widgets and query.widgets.primary:
                        for w in query.widgets.primary:
                            if str(w.uuid) == widget_uuid:
                                target_widget = w
                                break

                    if target_widget:
                        logger.info(
                            f"Updating widget {target_widget.name} ({widget_uuid}) with args: {input_args}"
                        )
                        yield update_widget_in_dashboard(
                            widget_uuid=widget_uuid,
                            origin=target_widget.origin,
                            widget_id=target_widget.widget_id,
                            input_args=input_args,
                        )
                    else:
                        # Widget not found in context - use artifact-provided values as fallback
                        origin = artifact.get("origin")
                        widget_id = artifact.get("widget_id")

                        if origin and widget_id:
                            logger.warning(
                                f"Widget {widget_uuid} not in context, using artifact values"
                            )
                            yield update_widget_in_dashboard(
                                widget_uuid=widget_uuid,
                                origin=origin,
                                widget_id=widget_id,
                                input_args=input_args,
                            )
                        else:
                            logger.error(
                                f"Cannot update widget {widget_uuid}: not in context and missing origin/widget_id"
                            )
                            yield sse_message_chunk(
                                f"\n\n*Error: Widget {widget_uuid} not found in dashboard context.*"
                            )
                elif artifact_type == "widget_add":
                    widget_id = artifact.get("widget_id")
                    input_args = artifact.get("input_args", {})
                    origin = artifact.get("origin", "ViaNexus Widgets")

                    if not widget_id:
                        logger.error("widget_add artifact missing widget_id")
                        continue

                    logger.info(f"Adding widget {widget_id} with args: {input_args}")
                    yield add_widget_to_dashboard(
                        origin=origin,
                        widget_id=widget_id,
                        input_args=input_args,
                    )
                else:
                    logger.warning(f"Unknown artifact type: {artifact_type}")

            # Include session info in final message if needed
            if new_session_id:
                session_store[token] = new_session_id
                logger.info(f"Session ID: {new_session_id}")

            # Yield citations at the end if we have any
            if citations_list:
                logger.info(f"Yielding {len(citations_list)} citations")
                yield citations(citations_list).model_dump()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from financial agent: {e}")
        yield sse_message_chunk(f"Error communicating with financial agent: {e}")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        yield sse_message_chunk(f"Failed to reach financial agent: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        yield sse_message_chunk(f"An unexpected error occurred: {e}")
