"""Shared output helpers for CLI commands that present model metadata.

These back the ``ftm ref`` command group, which has two audiences: a human at
a terminal who wants a scannable table, and a coding agent (or ``jq``) that
wants machine-readable JSON. Reach for these instead of hand-rolling output so
every ``ref`` subcommand decides JSON-vs-table the same way."""

import sys
import orjson
from typing import Any, List, Optional, Sequence

from rich.console import Console
from rich.table import Table


def is_json_mode(json_flag: bool) -> bool:
    """Decide whether to emit JSON rather than a table.

    JSON wins when ``--json`` is passed explicitly, or whenever stdout is not a
    terminal (piped or redirected) — so ``ftm ref schema Person | jq`` works
    without the caller remembering the flag."""
    return json_flag or not sys.stdout.isatty()


def emit_json(data: Any) -> None:
    """Write ``data`` to stdout as indented, key-sorted JSON with a newline."""
    opt = orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS | orjson.OPT_APPEND_NEWLINE
    sys.stdout.buffer.write(orjson.dumps(data, option=opt))


def print_table(
    rows: Sequence[Sequence[Any]],
    headers: Sequence[str],
    title: Optional[str] = None,
    caption: Optional[str] = None,
) -> None:
    """Render ``rows`` as a rich table on stdout.

    Used by the table (non-JSON) path of ``ref`` commands. ``caption`` is shown
    below the table — a good place for a count or a clarifying footnote. Cell
    values are stringified; ``None`` renders as an empty cell."""
    table = Table(title=title, caption=caption, header_style="bold")
    for header in headers:
        table.add_column(header)
    for row in rows:
        cells: List[str] = ["" if c is None else str(c) for c in row]
        table.add_row(*cells)
    Console().print(table)
