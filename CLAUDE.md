# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nexus-agent is an OpenBB-compatible interface layer that bridges OpenBB Workspace to the viaNexus financial agent ecosystem. It transforms OpenBB's SSE-based protocol to communicate with the financial-chat-agent backend.

```
OpenBB → nexus-agent → financial-chat-agent → viaNexus SDK → MCP server
              │               │                    │              │
        SSE adapter    client_context      X-Tool-Categories   tags filter
                       {type:"openbb"}     header routing      (tool filtering)
```

## Commands

```bash
# Install dependencies (uses uv)
uv sync

# Install dev dependencies (linting, testing)
uv sync --extra dev

# Run the development server
uv run python main.py
# Or using the script entry point:
uv run nexus-agent

# The server runs on port 8001 by default

# Linting
uv run ruff check .
uv run ruff format .

# Testing
uv run pytest
```

## Architecture

### This Service (nexus-agent)
- **Single file service** (`main.py`) - FastAPI app with SSE streaming
- Transforms OpenBB `/query` requests into financial-chat-agent `/chat` calls
- Automatically injects `client_context: {type: "openbb"}` to enable OpenBB-specific MCP tools
- Streams responses back as SSE events (message_chunk, chart, table, reasoning_step)

### OpenBB Contract
- `GET /agents.json` - Agent metadata for OpenBB discovery
- `POST /query` - SSE streaming endpoint accepting `QueryRequest` with messages
- Requires `token` query parameter for authentication
- Optional `session_id` for conversation continuity

### OpenBB Message Structure Issues

**CRITICAL**: OpenBB sends `QueryRequest` messages with structural issues that must be preprocessed before Pydantic validation:

1. **`extra_state` field**: OpenBB sends `extra_state: null` but the schema requires `extra_state: {}` (dict)
2. **Extra `items` wrapper**: Tool result messages (role: "tool") have an incorrect nesting:
   ```json
   // OpenBB sends:
   {"data": [{"items": [{"status": "success", "message": "..."}]}]}

   // Schema expects:
   {"data": [{"status": "success", "message": "..."}]}
   ```
3. **Missing `extra_citations`**: `DataContent` structures often lack the required `extra_citations: []` field

**Fix Applied**: The `/query` endpoint preprocesses requests using `fix_openbb_message_structure()` before validation (see main.py:105-145). This function:
- Replaces `extra_state: null` with `extra_state: {}`
- Unwraps the extra `items` layer for `ClientCommandResult` messages
- Adds missing `extra_citations: []` to `DataContent` structures

Without this preprocessing, requests fail with 422 validation errors.

### Related Repositories
This service is part of a multi-repo architecture:
- **financial-chat-agent** (`~/code/bluesky/financial-chat-agent`) - LLM agent with MCP client
- **viaNexus-agent-sdk-python** (`~/code/bluesky/viaNexus-agent-sdk-python`) - SDK handling MCP connections
- **mcp-service** (`~/code/bluesky/mcp-service`) - MCP server with financial data tools

### Tool Filtering
The `client_context.type = "openbb"` triggers the SDK to send `X-Tool-Categories: financial,openbb` header to the MCP server, which then returns OpenBB-specific tools in addition to standard financial tools.

**OpenBB-specific MCP tools** (tagged `{"openbb"}`):
- `create_chart` - Returns chart artifact for visualization
- `create_table` - Returns table artifact for visualization
- `fetch_and_chart` - Fetches data and creates chart in one call
- `update_widget` - Updates existing dashboard widget parameters

### Widget Update Flow
When the LLM needs to update a widget on the OpenBB dashboard:

1. **Widget metadata** is passed in context to the LLM (uuid, origin, widget_id, current params)
2. **LLM calls** `update_widget` MCP tool with widget_uuid and new input_args
3. **MCP returns** artifact with `artifact_type: "widget_update"`
4. **SDK captures** artifact (detects `artifact_type` field)
5. **nexus-agent** handles artifact, looks up widget by UUID, yields `update_widget_in_dashboard()` SSE event
6. **OpenBB** receives SSE event and updates the widget

### Artifact System
MCP tools can return artifacts (structured data) that flow back through the system:

```python
# MCP tool returns JSON with artifact_type marker
{"artifact_type": "chart", "data": [...], "x_key": "date", ...}
{"artifact_type": "table", "data": [...], "name": "..."}
{"artifact_type": "widget_update", "widget_uuid": "...", "input_args": {...}}
```

The SDK captures these (checks for `artifact_type` field), passes them through financial-chat-agent, and nexus-agent converts them to OpenBB SSE events.

### Two-Phase Widget Data Retrieval
When widgets are in the dashboard context:
1. **Phase 1**: Human message + widgets present → nexus-agent yields `get_widget_data()` to fetch widget data
2. **Phase 2**: Tool callback with widget data → extract context, add widget metadata, call LLM

## Key Source Files

- **`main.py`** - FastAPI app, `/query` endpoint, SSE streaming setup
- **`src/agent/stream_response.py`** - Core streaming logic, widget data phases, artifact handling
- **`src/agent/widget_context.py`** - Formats widget metadata for LLM context
- **`src/agent/widget_discovery.py`** - Widget catalog and discovery
- **`src/utils/sse.py`** - SSE helpers: `sse_message_chunk()`, `update_widget_in_dashboard()`, `add_widget_to_dashboard()`
- **`src/config.py`** - Environment configuration
- **`src/widgets/`** - Widget implementations (stock_stats, stock_chart, rules)

## Environment Variables

- `FINANCIAL_AGENT_URL` - URL of financial-chat-agent (default: `http://localhost:8501`)
- `AGENT_NAME` - Display name for OpenBB (default: "viaNexus Financial Agent")
- `AGENT_DESCRIPTION` - Agent description for OpenBB discovery

## OpenBB SSE Integration - Critical Notes

**IMPORTANT**: When implementing SSE streaming for OpenBB, follow this exact pattern:

### Correct SSE Pattern
```python
from openbb_ai import message_chunk  # Import directly from openbb_ai, NOT openbb_ai.helpers

async def stream():
    yield message_chunk("Hello").model_dump(exclude_none=True)
    yield message_chunk(" World").model_dump(exclude_none=True)
    # NO done event - generator just ends naturally

return EventSourceResponse(content=stream(), media_type="text/event-stream")
```

### Common Pitfalls (all cause "An error has occurred" in OpenBB)

1. **DON'T yield a "done" event** - OpenBB doesn't expect it. Just let the generator end.
2. **DON'T manually create SSE dicts** - Use `openbb_ai.message_chunk()`
3. **DON'T forget `model_dump(exclude_none=True)`** - The Pydantic model must be serialized
4. **DON'T import from `openbb_ai.helpers`** - Import directly from `openbb_ai`
5. **DO use `content=` parameter** in EventSourceResponse (not positional arg)
