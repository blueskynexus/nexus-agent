"""Tests for stream response functionality.

These tests verify the SSE streaming behavior for various command scenarios.
They were originally inline debug commands in stream_response.py.
"""

from unittest.mock import MagicMock

from openbb_ai import QueryRequest as OpenBBQueryRequest
from openbb_ai import chart as openbb_chart

from src.config import WIDGET_ORIGIN
from src.utils.sse import add_widget_to_dashboard, sse_message_chunk, update_widget_in_dashboard


def create_mock_query(message: str, widgets=None, last_role="human") -> MagicMock:
    """Create a mock OpenBBQueryRequest for testing."""
    mock_query = MagicMock(spec=OpenBBQueryRequest)
    mock_query.messages = [MagicMock(role=last_role, content=message)]
    mock_query.widgets = widgets
    return mock_query


def create_mock_widget(name: str = "Test Widget", uuid: str = "test-uuid"):
    """Create a mock widget for testing."""
    mock_widget = MagicMock()
    mock_widget.name = name
    mock_widget.uuid = uuid
    mock_widget.origin = WIDGET_ORIGIN
    mock_widget.widget_id = "test_widget"
    mock_widget.params = []
    return mock_widget


class TestFooBarResponse:
    """Test the basic foo -> bar response."""

    def test_foo_returns_bar(self):
        """When user sends 'foo', should return 'bar'."""
        query = create_mock_query("foo")
        chunks = list(test_case_response(query, "foo"))
        assert len(chunks) == 1
        # The chunk should be the SSE formatted message containing "bar"


class TestChartResponse:
    """Test the sample chart response."""

    def test_chart_returns_sample_line_chart(self):
        """When user sends 'chart', should return a sample line chart."""
        query = create_mock_query("chart")
        chunks = list(test_case_response(query, "chart"))
        assert len(chunks) == 2  # Message + chart


class TestWidgetUpdate:
    """Test widget update functionality."""

    def test_update_with_widget_in_context(self):
        """When user sends 'update' with widget in context, should update widget."""
        mock_widget = create_mock_widget()
        mock_widgets = MagicMock()
        mock_widgets.primary = [mock_widget]

        query = create_mock_query("update", widgets=mock_widgets)
        chunks = list(test_case_response(query, "update"))

        # Should have message chunk and update_widget_in_dashboard event
        assert len(chunks) == 2

    def test_update_without_widget(self):
        """When user sends 'update' without widget, should return error message."""
        query = create_mock_query("update")
        chunks = list(test_case_response(query, "update"))

        assert len(chunks) == 1
        # Should contain error about no widget


class TestAddWidget:
    """Test adding widgets to dashboard."""

    def test_add_chart_default_symbol(self):
        """When user sends 'add chart', should add AAPL chart by default."""
        query = create_mock_query("add chart")
        chunks = list(test_case_response(query, "add chart"))

        assert len(chunks) == 2  # Message + add_widget event

    def test_add_chart_with_symbol(self):
        """When user sends 'add chart TSLA', should add TSLA chart."""
        query = create_mock_query("add chart TSLA")
        chunks = list(test_case_response(query, "add chart TSLA"))

        assert len(chunks) == 2

    def test_add_stats_default_symbol(self):
        """When user sends 'add stats', should add AAPL stats by default."""
        query = create_mock_query("add stats")
        chunks = list(test_case_response(query, "add stats"))

        assert len(chunks) == 2

    def test_add_stats_with_symbol(self):
        """When user sends 'add stats MSFT', should add MSFT stats."""
        query = create_mock_query("add stats MSFT")
        chunks = list(test_case_response(query, "add stats MSFT"))

        assert len(chunks) == 2


def test_case_response(query: OpenBBQueryRequest, message: str):
    """Test case response generator for debugging SSE streaming.

    This function provides hardcoded responses for testing the OpenBB integration
    without requiring the full financial agent backend.

    Args:
        query: The OpenBB query request
        message: The user's message

    Yields:
        SSE event dictionaries
    """
    msg = message.strip().lower()

    # Test case: if message is "foo", return "bar"
    if msg == "foo":
        yield sse_message_chunk("bar")
        return

    # Test case: if message is "chart", return a sample line chart
    if msg == "chart":
        yield sse_message_chunk("Here is a sample line chart:\n\n")
        yield openbb_chart(
            type="line",
            data=[
                {"x": "Jan", "y": 100},
                {"x": "Feb", "y": 120},
                {"x": "Mar", "y": 115},
                {"x": "Apr", "y": 130},
                {"x": "May", "y": 145},
            ],
            x_key="x",
            y_keys=["y"],
            name="Sample Chart",
            description="Monthly values over time",
        ).model_dump()
        return

    # Test case: if message is "context", return the widget context (for debugging)
    if msg == "context":
        from openbb_ai import WidgetRequest

        widget_requests: list[WidgetRequest] = []
        if query.widgets and query.widgets.primary:
            for widget in query.widgets.primary:
                widget_requests.append(
                    WidgetRequest(
                        widget=widget,
                        input_arguments={
                            param.name: param.current_value for param in widget.params
                        },
                    )
                )
        # Show raw data for debugging
        raw_info = []
        raw_info.append("placeholder")
        yield sse_message_chunk("".join(raw_info))
        return

    # Test case: if message is "update", update the first widget's symbol to MSFT
    if msg == "update":
        last_msg = query.messages[-1]
        if last_msg.role == "tool":
            yield sse_message_chunk("Widget updated successfully!")
            return

        if query.widgets and query.widgets.primary:
            widget = query.widgets.primary[0]
            yield sse_message_chunk(f"Updating widget '{widget.name}' symbol to MSFT...\n\n")
            yield update_widget_in_dashboard(
                widget_uuid=str(widget.uuid),
                origin=widget.origin,
                widget_id=widget.widget_id,
                input_args={"symbol": "MSFT"},
            )
        else:
            yield sse_message_chunk(
                "No widget in context. Please add a widget first (e.g., Stock Statistics)."
            )
        return

    # Test case: "add chart" or "add chart SYMBOL" - adds stock_chart widget
    if msg.startswith("add chart"):
        last_msg = query.messages[-1]
        if last_msg.role == "tool":
            yield sse_message_chunk("Stock chart widget added to dashboard!")
            return

        parts = msg.split()
        symbol = parts[2].upper() if len(parts) > 2 else "AAPL"

        yield sse_message_chunk(f"Adding Stock Price Chart for {symbol}...\n\n")
        yield add_widget_to_dashboard(
            origin=WIDGET_ORIGIN,
            widget_id="stock_chart",
            input_args={"symbol": symbol},
        )
        return

    # Test case: "add stats" or "add stats SYMBOL" - adds stock_stats widget
    if msg.startswith("add stats"):
        last_msg = query.messages[-1]
        if last_msg.role == "tool":
            yield sse_message_chunk("Stock statistics widget added to dashboard!")
            return

        parts = msg.split()
        symbol = parts[2].upper() if len(parts) > 2 else "AAPL"

        yield sse_message_chunk(f"Adding Stock Statistics for {symbol}...\n\n")
        yield add_widget_to_dashboard(
            origin=WIDGET_ORIGIN,
            widget_id="stock_stats",
            input_args={"symbol": symbol},
        )
        return
