"""MCP-to-ADK tool adapter for wrapping MCP server tools as FunctionTools."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from typing import Any

from google.adk.tools import FunctionTool

from config.settings import get_settings

logger = logging.getLogger(__name__)


class McpToolAdapter:
    """Wraps MCP server tools as ADK ``FunctionTool`` instances.

    Loads server configuration from ``config/mcp_servers.yaml`` and spawns
    stdio subprocesses per invocation (connection pooling in production).
    """

    def __init__(self, auth_token: str | None = None) -> None:
        settings = get_settings()
        self._auth_token = auth_token or settings.mcp_auth_token
        self._tool_cache: dict[str, FunctionTool] = {}

    def wrap_tool(
        self,
        server_name: str,
        tool_name: str,
        handler: Callable[..., Any] | None = None,
    ) -> FunctionTool:
        """Create or retrieve a cached ``FunctionTool`` for an MCP tool.

        Args:
            server_name: MCP server identifier (e.g. ``document_mcp``).
            tool_name: Tool name exposed by the MCP server.
            handler: Optional callable override; defaults to stub invoker.

        Returns:
            ADK ``FunctionTool`` ready for agent ``tools`` lists.
        """
        cache_key = f"{server_name}.{tool_name}"
        if cache_key in self._tool_cache:
            return self._tool_cache[cache_key]

        func = handler or self._make_stub_invoker(server_name, tool_name)
        func.__name__ = f"{server_name}_{tool_name}"
        func.__doc__ = (
            f"Invoke MCP tool '{tool_name}' on server '{server_name}'. "
            "Stub implementation — wire to MCP stdio transport in production."
        )

        tool = FunctionTool(func=func)
        self._tool_cache[cache_key] = tool
        return tool

    def wrap_server_tools(
        self,
        server_name: str,
        tool_names: Sequence[str],
    ) -> list[FunctionTool]:
        """Wrap multiple tools from a single MCP server."""
        return [self.wrap_tool(server_name, name) for name in tool_names]

    def _make_stub_invoker(
        self,
        server_name: str,
        tool_name: str,
    ) -> Callable[..., dict[str, Any]]:
        def invoke(**kwargs: Any) -> dict[str, Any]:
            logger.debug(
                "MCP stub invoke: server=%s tool=%s args=%s",
                server_name,
                tool_name,
                list(kwargs.keys()),
            )
            return {
                "status": "stub",
                "server": server_name,
                "tool": tool_name,
                "result": None,
            }

        return invoke


def create_mcp_tools(
    server_name: str,
    tool_names: Sequence[str],
) -> list[FunctionTool]:
    """Convenience factory for MCP-backed ADK tools.

    Args:
        server_name: MCP server identifier.
        tool_names: Tool names to expose to agents.

    Returns:
        List of ``FunctionTool`` instances.
    """
    adapter = McpToolAdapter()
    return adapter.wrap_server_tools(server_name, tool_names)
