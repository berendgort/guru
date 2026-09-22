"""MCP console-script entry points."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time


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
    host = os.environ.get("GURU_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("GURU_MCP_PORT", "8000"))
    print(f"guru-mcp-http listening on http://{host}:{port}/mcp/", flush=True)
    mcp.run(transport="http", host=host, port=port)


def run_tunnel() -> None:
    """Start local HTTP MCP + Cloudflare quick tunnel for Claude Cowork / claude.ai.

    Claude Code / Claude cloud sandboxes cannot reach windguru.cz. This exposes
    your laptop's guru-mcp-http over public HTTPS so Anthropic can dial *you*
    (you still call Windguru from your network).
    """
    cloudflared = shutil.which("cloudflared")
    if not cloudflared:
        print(
            "cloudflared not found on PATH.\n"
            "Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/\n"
            "Then: guru-mcp-tunnel",
            file=sys.stderr,
        )
        sys.exit(1)

    host = os.environ.get("GURU_MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("GURU_MCP_PORT", "8000"))

    def _port_open() -> bool:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            return s.connect_ex((host, port)) == 0

    if _port_open():
        print(f"Reusing existing MCP HTTP on http://{host}:{port}/mcp/", flush=True)
    else:

        def _serve() -> None:
            try:
                from guru.mcp.server import mcp
            except ModuleNotFoundError:
                print(
                    "MCP dependencies are not installed.\n"
                    "Install them with:  pip install 'windguru[mcp]'",
                    file=sys.stderr,
                )
                os._exit(1)
            # Quiet banner -- tunnel output is what the user needs.
            os.environ.setdefault("FASTMCP_SHOW_SERVER_BANNER", "false")
            mcp.run(transport="http", host=host, port=port)

        thread = threading.Thread(target=_serve, name="guru-mcp-http", daemon=True)
        thread.start()
        for _ in range(40):
            if _port_open():
                break
            time.sleep(0.15)
        else:
            print(
                f"guru-mcp-http failed to listen on {host}:{port}",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"guru-mcp-http listening on http://{host}:{port}/mcp/", flush=True)

    cmd = [
        cloudflared,
        "tunnel",
        "--url",
        f"http://{host}:{port}",
        "--no-autoupdate",
    ]
    print(
        "Starting Cloudflare quick tunnel…\n"
        "Paste the printed https://…/mcp/ URL into Claude → Customize → "
        "Connectors → Add custom connector.\n"
        "Leave this process running while you chat.\n",
        flush=True,
    )
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    url_re = re.compile(r"(https://[a-z0-9-]+\.trycloudflare\.com)")
    published: str | None = None
    try:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            if published is None:
                m = url_re.search(line)
                if m:
                    published = m.group(1).rstrip("/") + "/mcp/"
                    print(
                        "\n"
                        "══════════════════════════════════════════════\n"
                        f"  Claude custom connector URL:\n"
                        f"  {published}\n"
                        "══════════════════════════════════════════════\n",
                        flush=True,
                    )
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        print("\nTunnel stopped.", flush=True)
        sys.exit(0)
