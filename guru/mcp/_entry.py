"""MCP console-script entry points."""

from __future__ import annotations

import sys


def run() -> None:
    try:
        from guru.mcp.server import mcp
    except ModuleNotFoundError:
        print(
            "MCP dependencies are not installed.\n"
            "Install them with:  pip install 'windguru[mcp]'",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run()


def run_http() -> None:
    try:
        from guru.mcp.server import mcp
    except ModuleNotFoundError:
        print(
            "MCP dependencies are not installed.\n"
            "Install them with:  pip install 'windguru[mcp]'",
            file=sys.stderr,
        )
        sys.exit(1)
    mcp.run(transport="http", host="127.0.0.1", port=8000)
