"""Integration tests for MCP server registry configuration."""

from pathlib import Path

import yaml


def test_mcp_servers_yaml_lists_five_servers():
    config_path = Path("config/mcp_servers.yaml")
    assert config_path.exists()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    servers = data["servers"]
    expected = {
        "document_mcp",
        "rag_mcp",
        "gov_resources_mcp",
        "calendar_mcp",
        "audit_mcp",
    }
    assert set(servers.keys()) == expected


def test_each_mcp_server_has_stdio_command():
    config_path = Path("config/mcp_servers.yaml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    for name, cfg in data["servers"].items():
        assert cfg["transport"] == "stdio", f"{name} should use stdio"
        assert cfg["command"] == "python"
        assert cfg["args"], f"{name} missing module args"
