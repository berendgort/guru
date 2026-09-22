"""Windguru host patterns for sandbox / proxy allowlists.

One source of truth for Claude, Codex, and cloud environment UIs.
"""

from __future__ import annotations

__all__ = (
    "WINDGURU_HOSTS",
    "WINDGURU_CODEX_DOMAINS",
    "WINDGURU_CLOUD_DOMAINS",
)

# Claude sandbox.allowedDomains (* = subdomain wildcard).
WINDGURU_HOSTS = (
    "www.windguru.cz",
    "windguru.cz",
    "*.windguru.cz",
    "www.windguru.net",
    "windguru.net",
    "*.windguru.net",
)

# Codex / ChatGPT Work network_proxy (** = apex + subdomains).
WINDGURU_CODEX_DOMAINS = (
    "**.windguru.cz",
    "**.windguru.net",
    "www.windguru.cz",
    "www.windguru.net",
    "windguru.cz",
    "windguru.net",
)

# ChatGPT Work / Codex cloud environment UI allowlist (no ** syntax).
WINDGURU_CLOUD_DOMAINS = (
    "windguru.cz",
    "www.windguru.cz",
    "*.windguru.cz",
    "windguru.net",
    "www.windguru.net",
    "*.windguru.net",
)
