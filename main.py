"""
nexus-agent: OpenBB-compatible interface for viaNexus financial agent.

This service provides an SSE streaming interface compatible with OpenBB Workspace,
forwarding requests to the nexus-financial-agent with appropriate client context.
It also serves OpenBB widgets directly.
"""

import json
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openbb_ai import QueryRequest as OpenBBQueryRequest
from sse_starlette.sse import EventSourceResponse

from registry import WIDGETS
from src.agent.stream_response import stream_response
from src.config import settings
from src.utils.logging import configure_logging
from src.utils.sse import extract_token, sse_message_chunk
from src.widgets.dividends_table import dividends_table
from src.widgets.news import get_news
from src.widgets.rules import get_rules
from src.widgets.stock_chart import get_stock_chart
from src.widgets.stock_stats import get_stock_stats
from src.widgets.table import table_widget

logger = logging.getLogger(__name__)

# Initialize logging
configure_logging()

app = FastAPI(
    title="nexus-agent",
    description="OpenBB-compatible interface for viaNexus financial agent with integrated widgets",
    version="0.1.0",
)

# CORS configuration for OpenBB origins
origins = ["https://pro.openbb.co", "https://pro.openbb.dev", "http://localhost:1420"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage: maps token -> session_id
session_store: dict[str, str] = {}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log validation errors with full details."""
    body = await request.body()
    logger.error(f"Validation error for {request.url}")
    logger.error(f"Request body: {body.decode('utf-8') if body else 'empty'}")
    logger.error(f"Validation errors: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# --- Agent Endpoints ---
@app.get("/agents.json")
async def get_agents_metadata() -> JSONResponse:
    """Return agent metadata for OpenBB discovery."""
    return JSONResponse(
        {
            "vianexus-financial-agent": {
                "name": settings.agent_name,
                "description": settings.agent_description,
                "image": "https://github.com/OpenBB-finance/copilot-for-terminal-pro/assets/14093308/7da2a512-93b9-478d-90bc-b8c3dd0cabcf",
                "endpoints": {"query": "/query"},
                "features": {
                    "streaming": True,
                    "widget-dashboard-select": True,
                    "widget-dashboard-search": True,
                },
            }
        }
    )


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


def fix_openbb_message_structure(data: dict) -> dict:
    """
    Fix OpenBB message structure to match QueryRequest schema.

    OpenBB sends tool results with an extra 'items' wrapper that needs to be unwrapped,
    and sets extra_state to None instead of {} or omitting it.
    """
    if "messages" not in data:
        return data

    for msg in data["messages"]:
        # Fix tool result messages (role: "tool")
        if msg.get("role") == "tool" and "data" in msg:
            # Fix extra_state: None -> {}
            if msg.get("extra_state") is None:
                msg["extra_state"] = {}

            # Fix data items
            for i, item in enumerate(msg["data"]):
                if not isinstance(item, dict):
                    continue

                # Case 1: Unwrap extra 'items' layer for ClientCommandResult
                # {"items": [{"status": "success", ...}]} -> {"status": "success", ...}
                if "items" in item and "status" not in item and "content" not in item:
                    items_array = item.get("items", [])
                    if len(items_array) > 0:
                        first_item = items_array[0]
                        # Check if it's a ClientCommandResult (has 'status' field)
                        if isinstance(first_item, dict) and "status" in first_item:
                            msg["data"][i] = first_item
                        # Otherwise it might be DataContent - add extra_citations if missing
                        elif isinstance(first_item, dict) and "content" in first_item:
                            if "extra_citations" not in item:
                                item["extra_citations"] = []

                # Case 2: Ensure DataContent has extra_citations
                if "items" in item and "extra_citations" not in item:
                    item["extra_citations"] = []

    return data


@app.post("/query")
async def query(
    request: Request,
    token: str | None = Query(None, description="Authentication token"),
    session_id: str | None = Query(None, description="Session ID for conversation continuity"),
) -> EventSourceResponse:
    """
    Main chat endpoint for OpenBB.

    Accepts a OpenBBQueryRequest with messages, forwards to the financial agent
    with OpenBB client context, and streams the response as SSE events.
    """
    # Read and parse request body manually to fix structure before validation
    try:
        body = await request.body()
        data = json.loads(body)

        # Fix OpenBB's incorrect message structure
        data = fix_openbb_message_structure(data)

        # Now parse with Pydantic validation
        query_request = OpenBBQueryRequest(**data)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in request body: {e}"

        async def error_stream():
            yield sse_message_chunk(error_msg)

        return EventSourceResponse(content=error_stream(), media_type="text/event-stream")
    except Exception as e:
        error_msg = f"Error parsing request: {e}"

        async def error_stream():
            yield sse_message_chunk(error_msg)

        return EventSourceResponse(content=error_stream(), media_type="text/event-stream")

    # Extract token from various sources
    effective_token = extract_token(request, token)

    if not effective_token:
        # Return error as SSE stream
        async def error_stream():
            yield sse_message_chunk(
                "Authentication token is required. Please configure a token when adding the agent."
            )

        return EventSourceResponse(content=error_stream(), media_type="text/event-stream")

    financial_agent_session_id = session_store.get(effective_token) or None

    return EventSourceResponse(
        content=stream_response(
            query_request, effective_token, financial_agent_session_id, session_store
        ),
        media_type="text/event-stream",
    )


# --- Widget Endpoints ---
@app.get("/widgets.json")
def get_widgets() -> JSONResponse:
    """Widgets configuration file for OpenBB Workspace.

    Returns:
        JSONResponse: The WIDGETS dictionary containing all registered widgets.
    """
    return JSONResponse(content=WIDGETS)


@app.get("/apps.json")
def get_apps() -> JSONResponse:
    """Apps configuration file for OpenBB Workspace.

    Returns:
        JSONResponse: The contents of apps.json file.
    """
    return JSONResponse(
        content=json.load((Path(__file__).parent / "src" / "documents" / "apps.json").open())
    )


# Register widget routes with the FastAPI app
app.get("/stock_stats")(get_stock_stats)
app.get("/moving_average_crossover")(get_stock_chart)
app.get("/rules")(get_rules)
app.get("/vianexus_news")(get_news)
app.get("/table_widget")(table_widget)
app.get("/dividends_table")(dividends_table)


def run():
    """Run the server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    run()
