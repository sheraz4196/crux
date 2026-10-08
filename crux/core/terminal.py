import os
import shutil
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Capabilities:
    interactive: bool
    color: bool
    truecolor: bool
    unicode: bool
    width: int
    name: str


def detect(stream=None, no_color=False):
    stream = stream or sys.stdout
    interactive = stream.isatty()
    color = interactive and os.environ.get("TERM") != "dumb" and "NO_COLOR" not in os.environ and not no_color
    try:
        "📁├❯".encode(getattr(stream, "encoding", None) or "ascii")
        unicode = True
    except (UnicodeError, LookupError):
        unicode = False
    return Capabilities(interactive, color, color and os.environ.get("COLORTERM") in ("truecolor", "24bit"), unicode, shutil.get_terminal_size((80, 24)).columns, os.environ.get("TERM_PROGRAM", os.environ.get("TERM", "unknown")))
