"""MCP servers for the German Bureaucracy AI Agent."""

from config.settings import Settings, get_settings

SERVER_VERSION = "1.0.0"

__all__ = ["SERVER_VERSION", "Settings", "get_settings", "mcp_auth_token"]

__version__ = SERVER_VERSION


def mcp_auth_token() -> str:
    """Return the configured MCP bearer token."""
    return get_settings().mcp_auth_token
