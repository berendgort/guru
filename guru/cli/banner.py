"""Terminal brand mark for ``guru --help`` (Claude-style wordmark)."""

from __future__ import annotations

from rich.text import Text

from guru.cli.console import console
from guru.rider.voice import BANNER_TAG, joke, tagline

# Format A — bright neon ice (#67E8F9)
_BANNER_ROWS = (
    r"  ██████╗ ██╗   ██╗██████╗ ██╗   ██╗      ██████╗ ██╗      ██╗",
    r" ██╔════╝ ██║   ██║██╔══██╗██║   ██║     ██╔════╝ ██║      ██║",
    r" ██║  ███╗██║   ██║██████╔╝██║   ██║ ███ ██║      ██║      ██║",
    r" ██║   ██║██║   ██║██╔══██╗██║   ██║ ╚═╝ ██║      ██║      ██║",
    r" ╚██████╔╝╚██████╔╝██║  ██║╚██████╔╝     ╚██████╗ ███████╗ ██║",
    r"  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝      ╚═════╝ ╚══════╝ ╚═╝",
)

_AUTHOR = "Dr. Berend Gort"
_AUTHOR_URL = "https://www.berendgort.dev"
_AUTHOR_HOST = "www.berendgort.dev"

_STYLE = "bold #67E8F9"
_TAG = "italic #BAE6FD"
_CREDIT = "#7DD3FC"
_JOKE = "dim italic #A5F3FC"


def print_banner() -> None:
    """Print the GURU-CLI wordmark when stdout is a TTY (skip for pipes/JSON)."""
    if not console.is_terminal:
        return
    console.print()
    for row in _BANNER_ROWS:
        console.print(Text(row, style=_STYLE))
    console.print(Text(f"  {BANNER_TAG}", style=_TAG))
    console.print(Text(f"  {tagline(seed='help')} · {joke(seed='banner')}", style=_JOKE))
    credit = Text("  ", style=_CREDIT)
    credit.append(_AUTHOR, style=_CREDIT)
    credit.append("  ·  ", style=_CREDIT)
    credit.append(_AUTHOR_HOST, style=f"link {_AUTHOR_URL} underline {_CREDIT}")
    console.print(credit)
    console.print()
