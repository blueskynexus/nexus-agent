# viaNexus Financial Agent Ecosystem - Design Document

## Executive Summary

The viaNexus Financial Agent ecosystem is a multi-service architecture that connects the OpenBB Workspace to a sophisticated financial AI assistant. The system enables users to interact with financial data through natural language, receive real-time market insights, and dynamically manage dashboard widgets—all powered by LLM intelligence and MCP (Model Context Protocol) tooling.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OpenBB Workspace                                   │
│                     (Professional Financial Dashboard)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ SSE Streaming
                                    │ POST /query
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           nexus-agent                                        │
│                    (OpenBB Protocol Adapter)                                 │
│   • Transforms OpenBB requests to financial-chat-agent format               │
│   • Handles two-phase widget data retrieval                                 │
│   • Converts artifacts to SSE events for dashboard updates                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP + SSE
                                    │ POST /chat
                                    │ client_context: {type: "openbb"}
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       financial-chat-agent                                   │
│                      (LLM Orchestration Layer)                               │
│   • Claude/GPT orchestration with conversation memory                       │
│   • Routes tool calls through viaNexus SDK                                  │
│   • Manages session state and conversation context                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ MCP Protocol
                                    │ X-Tool-Categories: financial,openbb
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    viaNexus-agent-sdk-python                                 │
│                      (MCP Client Library)                                    │
│   • Translates client_context to tool category headers                      │
│   • Manages MCP server connections and tool discovery                       │
│   • Captures and passes artifacts back through the chain                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ MCP Protocol + HTTP
                                    │ Tool execution
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           mcp-service                                        │
│                    (Financial Tools MCP Server)                              │
│   • Financial data tools (quotes, charts, analytics)                        │
│   • OpenBB-specific tools (create_chart, update_widget, etc.)              │
│   • Tool filtering via tags: {"financial"}, {"openbb"}                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    External Data Sources                                     │
│           (Vianexus API, Market Data Providers, etc.)                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Use Case

### Primary Use Case: Conversational Financial Dashboard

Users of OpenBB Workspace can interact with a financial AI assistant that:

1. **Answers questions about market data** - "What's the PE ratio for Apple?"
2. **Generates visualizations** - "Show me a chart of MSFT's moving averages"
3. **Updates dashboard widgets dynamically** - "Change the symbol to GOOGL"
4. **Adds new widgets to the dashboard** - "Add a stock stats widget for Tesla"
5. **Provides contextual analysis** - Uses existing widget data to inform responses

### Key Capabilities

| Capability | Description | Enabled By |
|------------|-------------|------------|
| **Natural Language Queries** | Ask questions about financial data | LLM + MCP tools |
| **Widget Awareness** | AI understands what's on your dashboard | Two-phase widget data pattern |
| **Generative UI** | AI can modify dashboard programmatically | Artifact system + SSE events |
| **Tool Filtering** | Different clients get different tools | client_context + tool tags |
| **Real-time Streaming** | Responses stream as they're generated | SSE protocol |

---

## Service Descriptions

### 1. nexus-agent (This Repository)

**Role**: OpenBB Protocol Adapter

**Purpose**: Bridge between OpenBB Workspace's SSE-based protocol and the financial-chat-agent backend. This service is the entry point for all OpenBB requests.

**Key Responsibilities**:

- **Request Preprocessing**: Fix structural issues in OpenBB's message format before validation
- **Two-Phase Widget Data Retrieval**: Coordinate fetching widget data from the dashboard
- **Response Streaming**: Convert LLM responses to OpenBB-compatible SSE events
- **Artifact Handling**: Transform MCP tool artifacts into dashboard actions (charts, tables, widget updates)
- **Widget Registration**: Serve widget configurations and data endpoints

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agents.json` | GET | OpenBB agent discovery |
| `/query` | POST | Main chat endpoint (SSE streaming) |
| `/widgets.json` | GET | Widget configuration |
| `/apps.json` | GET | Predefined app layouts |
| `/stock_stats` | GET | Stock metrics widget data |
| `/moving_average_crossover` | GET | Chart widget data |
| `/rules` | GET | Rules table widget data |

**Technology**: FastAPI, Python, SSE (Server-Sent Events)

---

### 2. financial-chat-agent

**Role**: LLM Orchestration Layer

**Purpose**: Manage LLM interactions, conversation memory, and tool orchestration. This is the "brain" of the system.

**Key Responsibilities**:

- **LLM Integration**: Interface with Claude/GPT for natural language understanding
- **Conversation Memory**: Maintain context across multiple turns
- **Tool Routing**: Decide which MCP tools to call based on user intent
- **Context Injection**: Pass client_context to the SDK for tool filtering
- **Response Generation**: Combine LLM output with tool results

**How It Works**:

```
1. Receives request from nexus-agent with:
   - User message
   - client_context: {type: "openbb"}
   - widget_context: (optional) data from dashboard widgets

2. Sends to LLM with available tools from MCP server

3. LLM either:
   - Responds directly with text
   - Calls MCP tools (create_chart, update_widget, etc.)

4. Returns response with:
   - Text content
   - Artifacts from tool calls
   - Session ID for conversation continuity
```

**Technology**: Python, LangChain/custom orchestration, viaNexus SDK

---

### 3. viaNexus-agent-sdk-python

**Role**: MCP Client Library

**Purpose**: Provide a clean interface for connecting to MCP servers, managing tool discovery, and handling the client_context → tool filtering pipeline.

**Key Responsibilities**:

- **Tool Discovery**: Query MCP servers for available tools
- **Context Translation**: Convert `client_context.type` to `X-Tool-Categories` header
- **Tool Execution**: Call MCP tools and return results
- **Artifact Capture**: Detect and pass through artifact responses

**Tool Filtering Mechanism**:

```python
# In financial-chat-agent
client_context = {"type": "openbb"}

# SDK translates to header
headers = {"X-Tool-Categories": "financial,openbb"}

# MCP server filters tools by tag
# Returns only tools tagged with "financial" OR "openbb"
```

**Why This Matters**:

Different clients need different tool sets:
- **CLI users**: Basic financial tools
- **OpenBB users**: Financial tools + visualization tools (create_chart, update_widget)
- **API users**: Programmatic tools only

The SDK enables this filtering transparently.

**Technology**: Python, MCP Protocol

---

### 4. mcp-service

**Role**: Financial Tools MCP Server

**Purpose**: Provide the actual financial data tools that the LLM can call. This is where the business logic lives.

**Key Responsibilities**:

- **Tool Implementation**: Execute financial data queries, chart generation, etc.
- **Tool Filtering**: Return only tools matching requested categories
- **Artifact Generation**: Return structured artifacts for visualization
- **Data Integration**: Connect to Vianexus API and other data sources

**Tool Categories**:

| Tag | Tools | Available To |
|-----|-------|--------------|
| `financial` | `get_stock_quote`, `get_company_info`, `analyze_portfolio` | All clients |
| `openbb` | `create_chart`, `create_table`, `update_widget`, `fetch_and_chart` | OpenBB only |

**OpenBB-Specific Tools**:

| Tool | Purpose | Returns |
|------|---------|---------|
| `create_chart` | Generate chart visualization | Chart artifact |
| `create_table` | Generate table visualization | Table artifact |
| `update_widget` | Update widget parameters | Widget update artifact |
| `fetch_and_chart` | Fetch data and create chart in one call | Chart artifact |

**Artifact Structure**:

```json
{
  "artifact_type": "chart",
  "chart_type": "line",
  "data": [{"date": "2024-01-01", "price": 150.25}, ...],
  "x_key": "date",
  "y_keys": ["price"],
  "title": "AAPL Stock Price"
}
```

**Technology**: Python, MCP Protocol, FastAPI

---

## Data Flow Examples

### Example 1: Simple Question with Widget Context

**User asks**: "What's the current price?" (Stock Stats widget showing AAPL is on dashboard)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   OpenBB     │    │ nexus-agent  │    │   fin-chat   │    │ mcp-service  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │ POST /query       │                   │                   │
       │ + widgets: [...]  │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │ Phase 1: get_widget_data              │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │ Widget data       │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │ POST /chat        │                   │
       │                   │ + widget_context  │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ (No tools needed) │
       │                   │                   │                   │
       │                   │ Response: "The    │                   │
       │                   │ current price is  │                   │
       │                   │ $150.25"          │                   │
       │                   │<──────────────────│                   │
       │                   │                   │                   │
       │ SSE: message_chunk│                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
```

### Example 2: Chart Generation

**User asks**: "Show me a chart of Tesla's stock price"

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   OpenBB     │    │ nexus-agent  │    │   fin-chat   │    │ mcp-service  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │ POST /query       │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │ POST /chat        │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ create_chart()    │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ Chart artifact    │
       │                   │                   │<──────────────────│
       │                   │                   │                   │
       │                   │ Response +        │                   │
       │                   │ artifacts: [chart]│                   │
       │                   │<──────────────────│                   │
       │                   │                   │                   │
       │ SSE: message_chunk│                   │                   │
       │ SSE: chart        │                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │ Renders chart     │                   │                   │
       │ in conversation   │                   │                   │
```

### Example 3: Widget Update (Generative UI)

**User asks**: "Change the symbol to Microsoft"

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   OpenBB     │    │ nexus-agent  │    │   fin-chat   │    │ mcp-service  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │                   │
       │ POST /query       │                   │                   │
       │ + widgets: [      │                   │                   │
       │   {uuid: "abc",   │                   │                   │
       │    symbol: "AAPL"}│                   │                   │
       │ ]                 │                   │                   │
       │──────────────────>│                   │                   │
       │                   │                   │                   │
       │ (Phase 1 & 2)     │                   │                   │
       │<─────────────────>│                   │                   │
       │                   │                   │                   │
       │                   │ POST /chat        │                   │
       │                   │ widget_context:   │                   │
       │                   │ "UUID: abc,       │                   │
       │                   │  symbol: AAPL"    │                   │
       │                   │──────────────────>│                   │
       │                   │                   │                   │
       │                   │                   │ update_widget(    │
       │                   │                   │   uuid="abc",     │
       │                   │                   │   symbol="MSFT")  │
       │                   │                   │──────────────────>│
       │                   │                   │                   │
       │                   │                   │ Widget update     │
       │                   │                   │ artifact          │
       │                   │                   │<──────────────────│
       │                   │                   │                   │
       │                   │ Response +        │                   │
       │                   │ artifacts         │                   │
       │                   │<──────────────────│                   │
       │                   │                   │                   │
       │ SSE: update_widget│                   │                   │
       │<──────────────────│                   │                   │
       │                   │                   │                   │
       │ Updates widget    │                   │                   │
       │ symbol to MSFT    │                   │                   │
```

---

## Key Design Patterns

### 1. Two-Phase Widget Data Retrieval

**Problem**: The LLM needs to see widget data to answer questions about the dashboard, but the data lives in OpenBB.

**Solution**: A two-phase pattern where nexus-agent coordinates data retrieval:

```
Phase 1: nexus-agent detects widgets in request
         → Sends get_widget_data() SSE event
         → OpenBB fetches data from widget endpoints
         → OpenBB sends tool message with data

Phase 2: nexus-agent receives widget data
         → Extracts and formats for LLM context
         → Calls financial-chat-agent with widget_context
         → LLM can now reference dashboard data
```

### 2. Artifact-Driven UI Updates

**Problem**: How does the LLM modify the dashboard without direct access?

**Solution**: MCP tools return structured "artifacts" that flow back through the system:

```python
# MCP tool returns artifact
{
    "artifact_type": "widget_update",
    "widget_uuid": "abc-123",
    "input_args": {"symbol": "MSFT"}
}

# nexus-agent converts to SSE event
{
    "event": "function_call",
    "data": {
        "function": "update_widget_in_dashboard",
        "input_arguments": {...}
    }
}

# OpenBB receives and executes
```

### 3. Client Context Tool Filtering

**Problem**: Different clients need different tool sets.

**Solution**: Client context flows through the system and filters available tools:

```
OpenBB → nexus-agent:     client_context: {type: "openbb"}
nexus-agent → fin-chat:   client_context: {type: "openbb"}
fin-chat → SDK:           client_context: {type: "openbb"}
SDK → mcp-service:        X-Tool-Categories: financial,openbb
mcp-service:              Returns tools tagged "financial" OR "openbb"
```

### 4. Request Preprocessing

**Problem**: OpenBB sends requests that don't match the expected schema.

**Solution**: nexus-agent preprocesses requests before validation:

```python
def fix_openbb_message_structure(data):
    # Fix: extra_state: null → extra_state: {}
    # Fix: Unwrap nested items in tool results
    # Fix: Add missing extra_citations: []
    return fixed_data
```

---

## Technology Stack

| Service | Framework | Language | Protocol |
|---------|-----------|----------|----------|
| nexus-agent | FastAPI | Python | HTTP + SSE |
| financial-chat-agent | Custom/LangChain | Python | HTTP + SSE |
| viaNexus-agent-sdk | Library | Python | MCP |
| mcp-service | FastAPI | Python | MCP + HTTP |

---

## Configuration

### nexus-agent Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FINANCIAL_AGENT_URL` | `http://localhost:8501` | financial-chat-agent URL |
| `AGENT_NAME` | "viaNexus Financial Agent" | Display name in OpenBB |
| `AGENT_DESCRIPTION` | (see config.py) | Agent description |
| `VIANEXUS_API_KEY` | - | API key for Vianexus data |
| `VIANEXUS_BASE_URL` | `https://api.blueskyapi.com/v1` | Vianexus API base URL |

---

## Repository Locations

| Repository | Path | Purpose |
|------------|------|---------|
| nexus-agent | `~/code/bluesky/nexus-agent` | OpenBB adapter (this repo) |
| financial-chat-agent | `~/code/bluesky/financial-chat-agent` | LLM orchestration |
| viaNexus-agent-sdk-python | `~/code/bluesky/viaNexus-agent-sdk-python` | MCP client SDK |
| mcp-service | `~/code/bluesky/mcp-service` | MCP server with tools |

---

## Future Considerations

1. **Additional Widget Types**: Support for more visualization types (heatmaps, treemaps, etc.)
2. **Multi-Widget Operations**: Update multiple widgets in a single action
3. **Widget Templates**: Pre-built widget configurations for common use cases
4. **Enhanced Tool Filtering**: More granular control over tool availability
5. **Caching Layer**: Cache frequently requested financial data
6. **Authentication Improvements**: OAuth flow, token refresh handling
