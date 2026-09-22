"""Terminal brand mark for ``guru --help`` (Claude-style wordmark)."""

from __future__ import annotations

from rich.text import Text

from guru.cli.console import console

# Format A — bright neon ice (#67E8F9)
_BANNER_ROWS = (
    r"  ██████╗ ██╗   ██╗██████╗ ██╗   ██╗",
    r" ██╔════╝ ██║   ██║██╔══██╗██║   ██║",
    r" ██║  ███╗██║   ██║██████╔╝██║   ██║",
    r" ██║   ██║██║   ██║██╔══██╗██║   ██║",
    r" ╚██████╔╝╚██████╔╝██║  ██║╚██████╔╝",
    r"  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝",
)

_STYLE = "bold #67E8F9"
_TAG = "italic #BAE6FD"


def print_banner() -> None:
    """Print the GURU wordmark when stdout is a TTY (skip for pipes/JSON)."""
    if not console.is_terminal:
        return
    console.print()
    for row in _BANNER_ROWS:
        console.print(Text(row, style=_STYLE))
    console.print(
        Text(
            "  GURU-CLI  ·  kite spots · gear advice · thinking offloaded",
            style=_TAG,
        )
    )
    console.print()
