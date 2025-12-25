# ABOUTME: MCP server for the "Time Left" ChatGPT app.
# ABOUTME: Provides a single tool that returns time remaining in day/week/month/year.

from __future__ import annotations

import os
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List
import calendar

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Configuration
ROOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = ROOT_DIR.parent / "web"
TEMPLATE_URI = "ui://widget/main.html"
MIME_TYPE = "text/html+skybridge"

# Production deployment configuration
WIDGET_DOMAIN = os.environ.get("WIDGET_DOMAIN", "https://web-sandbox.oaiusercontent.com")
PORT = int(os.environ.get("PORT", 8000))


@lru_cache(maxsize=None)
def load_widget_html() -> str:
    """Load and cache the widget HTML."""
    html_path = ASSETS_DIR / "widget.html"
    return html_path.read_text(encoding="utf8")


def calculate_time_remaining() -> Dict[str, Any]:
    """Calculate elapsed and remaining percentages for day, week, month, and year."""
    now = datetime.now()

    # Day progress (midnight to midnight)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    day_elapsed_seconds = (now - day_start).total_seconds()
    day_total_seconds = 24 * 60 * 60
    day_percent = (day_elapsed_seconds / day_total_seconds) * 100

    # Week progress (Monday = 0)
    days_since_monday = now.weekday()
    week_start = day_start - timedelta(days=days_since_monday)
    week_elapsed_seconds = (now - week_start).total_seconds()
    week_total_seconds = 7 * 24 * 60 * 60
    week_percent = (week_elapsed_seconds / week_total_seconds) * 100

    # Month progress
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    month_end = month_start + timedelta(days=days_in_month)
    month_elapsed_seconds = (now - month_start).total_seconds()
    month_total_seconds = days_in_month * 24 * 60 * 60
    month_percent = (month_elapsed_seconds / month_total_seconds) * 100

    # Year progress
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_year = 366 if calendar.isleap(now.year) else 365
    year_elapsed_seconds = (now - year_start).total_seconds()
    year_total_seconds = days_in_year * 24 * 60 * 60
    year_percent = (year_elapsed_seconds / year_total_seconds) * 100

    return {
        "timestamp": now.isoformat(),
        "day": {
            "label": "Today",
            "elapsed": round(day_percent, 1),
            "remaining": round(100 - day_percent, 1),
            "detail": now.strftime("%A, %B %d"),
        },
        "week": {
            "label": "This Week",
            "elapsed": round(week_percent, 1),
            "remaining": round(100 - week_percent, 1),
            "detail": f"Week {now.isocalendar()[1]}",
        },
        "month": {
            "label": "This Month",
            "elapsed": round(month_percent, 1),
            "remaining": round(100 - month_percent, 1),
            "detail": now.strftime("%B %Y"),
        },
        "year": {
            "label": "This Year",
            "elapsed": round(year_percent, 1),
            "remaining": round(100 - year_percent, 1),
            "detail": str(now.year),
        },
    }


def tool_meta() -> Dict[str, Any]:
    """Return standard tool metadata with CSP for production deployment."""
    return {
        "openai/outputTemplate": TEMPLATE_URI,
        "openai/widgetAccessible": True,
        "openai/widgetCSP": {
            "connect_domains": [],      # Empty - widget doesn't make API calls
            "resource_domains": [],     # Empty - all assets are inline
        },
        "openai/widgetDomain": WIDGET_DOMAIN,
    }


# Initialize FastMCP with stateless HTTP mode
mcp = FastMCP(
    name="time-left",
    stateless_http=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


# Register widget as MCP resource
@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name="Time Left Widget",
            uri=TEMPLATE_URI,
            description="Progress bar visualization for time remaining",
            mimeType=MIME_TYPE,
            _meta=tool_meta(),
        )
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name="Time Left Widget",
            uriTemplate=TEMPLATE_URI,
            description="Progress bar visualization for time remaining",
            mimeType=MIME_TYPE,
            _meta=tool_meta(),
        )
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    """Handle resource read requests."""
    if str(req.params.uri) != TEMPLATE_URI:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    return types.ServerResult(
        types.ReadResourceResult(
            contents=[
                types.TextResourceContents(
                    uri=TEMPLATE_URI,
                    mimeType=MIME_TYPE,
                    text=load_widget_html(),
                    _meta=tool_meta(),
                )
            ]
        )
    )


# Register tool
@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name="get_time_remaining",
            title="Get Time Remaining",
            description="Use this when the user asks how much time is left in the day, week, month, or year, or asks about time remaining, time progress, or similar questions about elapsed time.",
            inputSchema={"type": "object", "properties": {}},
            _meta=tool_meta(),
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        ),
    ]


async def _handle_call_tool(req: types.CallToolRequest) -> types.ServerResult:
    """Handle tool invocations."""
    tool_name = req.params.name

    if tool_name == "get_time_remaining":
        time_data = calculate_time_remaining()

        # Widget data goes in structuredContent (becomes window.openai.toolOutput)
        # OpenAI directives go in _meta
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Here's your time progress: {time_data['day']['remaining']}% of today remains, {time_data['week']['remaining']}% of this week, {time_data['month']['remaining']}% of this month, and {time_data['year']['remaining']}% of {time_data['year']['detail']}.",
                    )
                ],
                structuredContent=time_data,  # All widget data here
                _meta=tool_meta(),
            )
        )

    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=f"Unknown tool: {tool_name}")],
            isError=True,
        )
    )


# Register handlers
mcp._mcp_server.request_handlers[types.CallToolRequest] = _handle_call_tool
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


# Create ASGI app with CORS
app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
except ImportError:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
