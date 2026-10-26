"""Smoke test for the MCP server wiring.

Skipped automatically unless the MCP 1.x SDK (which provides
`mcp.server.fastmcp.FastMCP`, as pinned in requirements.txt) is installed, so a
minimal or mismatched environment still runs the translation tests cleanly.
"""
import pytest

pytest.importorskip("mcp.server.fastmcp", reason="MCP 1.x (FastMCP) not installed")


def test_server_imports_and_exposes_tools():
    import server

    assert server.mcp is not None
    for name in ("translate", "detect_language", "list_languages"):
        assert getattr(server, name, None) is not None
