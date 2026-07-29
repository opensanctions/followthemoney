"""Shared output helpers for CLI commands that present model metadata.

These back the ``ftm ref`` command group, which has two audiences: a human at
a terminal who wants a scannable table, and a coding agent (or ``jq``) that
wants machine-readable JSON. Reach for these instead of hand-rolling output so
every ``ref`` subcommand decides JSON-vs-table the same way."""

import sys
from collections.abc import Sequence
from typing import Any

import orjson
from rich.console import Console
from rich.markdown import Markdown
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


#: Keys stripped from ``ref`` JSON regardless of value — storage and display
#: details (``maxLength``, ``plural``) and the ``pivot`` flag that an agent
#: reading the model to construct entities never needs.
BLANKET_DROP_KEYS = frozenset({"maxLength", "plural", "pivot"})

#: Keys stripped from ``ref`` JSON only when their value is ``False`` — a flag
#: at its default carries no information, but the ``True`` case is signal.
#: Targeted (not "every false boolean") so the rule never surprises us by
#: swallowing a future flag whose ``False`` case matters.
FALSE_DROP_KEYS = frozenset({"matchable", "abstract", "enum"})


def slim(data: Any) -> Any:
    """Recursively strip low-signal keys from a model payload before JSON output.

    The ``ref`` JSON exists mainly as context for a coding agent; flags at their
    default and storage trivia cost tokens without informing entity construction.
    Recurses so the per-property lists nested inside a schema payload are trimmed
    too. See ``BLANKET_DROP_KEYS`` and ``FALSE_DROP_KEYS`` for what goes; also
    drops a ``label`` that merely echoes ``name`` (e.g. schema ``Person``)."""
    if isinstance(data, dict):
        # A label identical to the name adds no information over the name alone.
        drop_label = (
            "name" in data and "label" in data and data["label"] == data["name"]
        )
        out = {}
        for key, value in data.items():
            if key in BLANKET_DROP_KEYS:
                continue
            if key in FALSE_DROP_KEYS and value is False:
                continue
            if key == "label" and drop_label:
                continue
            out[key] = slim(value)
        return out
    if isinstance(data, list):
        return [slim(item) for item in data]
    return data


def print_markdown(text: str) -> None:
    """Render a markdown description block to stdout.

    Schema, property, and type descriptions are authored in markdown; use this
    for the standalone description blocks in the `ref` detail views so emphasis,
    code spans, and lists format on a terminal. JSON output keeps the raw text."""
    Console().print(Markdown(text))


def print_table(
    rows: Sequence[Sequence[Any]],
    headers: Sequence[str],
    title: str | None = None,
    caption: str | None = None,
) -> None:
    """Render ``rows`` as a rich table on stdout.

    Used by the table (non-JSON) path of ``ref`` commands. ``caption`` is shown
    below the table — a good place for a count or a clarifying footnote. Cell
    values are stringified; ``None`` renders as an empty cell."""
    table = Table(title=title, caption=caption, header_style="bold")
    for header in headers:
        table.add_column(header)
    for row in rows:
        cells: list[str] = ["" if c is None else str(c) for c in row]
        table.add_row(*cells)
    Console().print(table)
