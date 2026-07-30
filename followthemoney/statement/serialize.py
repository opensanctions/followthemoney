import csv
import logging
from collections.abc import Generator, Iterable
from io import TextIOWrapper
from pathlib import Path
from types import TracebackType
from typing import BinaryIO, Self, TextIO, cast

import click
import orjson
from rigour.boolean import text_bool
from rigour.env import ENCODING

from followthemoney.statement.statement import Statement, StatementDict
from followthemoney.statement.util import unpack_prop
from followthemoney.util import ENTITY_VALUE_MAX, PROP_VALUE_MAX

log = logging.getLogger(__name__)

JSON = "json"
CSV = "csv"
PACK = "pack"
FORMATS = [JSON, CSV, PACK]

CSV_BATCH = 5000
CSV_COLUMNS = [
    "canonical_id",
    "entity_id",
    "prop",
    "prop_type",
    "schema",
    "value",
    "dataset",
    "origin",
    "lang",
    "original_value",
    "external",
    "first_seen",
    "last_seen",
    "id",
]
LEGACY_PACK_COLUMNS = [
    "entity_id",
    "prop",
    "value",
    "dataset",
    "lang",
    "original_value",
    "target",
    "external",
    "first_seen",
    "last_seen",
]
csv.field_size_limit(PROP_VALUE_MAX)


def read_json_statements(
    fh: BinaryIO,
    max_line: int = ENTITY_VALUE_MAX,
) -> Generator[Statement, None, None]:
    while line := fh.readline(max_line):
        data = orjson.loads(line)
        yield Statement.from_dict(data)


def read_csv_statements(fh: BinaryIO) -> Generator[Statement, None, None]:
    wrapped = TextIOWrapper(fh, encoding=ENCODING, newline="")
    for row in csv.DictReader(wrapped, dialect=csv.unix_dialect):
        data = cast(StatementDict, row)
        data["external"] = text_bool(row.get("external")) or False
        if row.get("lang") == "":
            data["lang"] = None
        if row.get("original_value") == "":
            data["original_value"] = None
        if row.get("origin") == "":
            data["origin"] = None
        if row.get("first_seen") == "":
            data["first_seen"] = None
        if row.get("last_seen") == "":
            data["last_seen"] = None
        if row.get("id") == "":
            data["id"] = None
        yield Statement.from_dict(data)


def read_pack_statements(fh: BinaryIO) -> Generator[Statement, None, None]:
    wrapped = TextIOWrapper(fh, encoding=ENCODING, newline="")
    yield from read_pack_statements_decoded(wrapped)


def read_pack_statements_decoded(fh: TextIO) -> Generator[Statement, None, None]:
    headers: list[str] | None = None
    for row in csv.reader(fh, dialect=csv.unix_dialect):
        if headers is None:
            if "entity_id" in row and "prop" in row:
                headers = row
                continue
            # This is a legacy pack file, with no headers. The current row
            # is data and must be processed, not skipped.
            headers = LEGACY_PACK_COLUMNS
        data = dict(zip(headers, row))
        try:
            schema, _, prop = unpack_prop(data["prop"])
        except TypeError:
            log.error("Invalid property in pack statement: {}".format(data["prop"]))
            continue
        yield Statement(
            entity_id=data["entity_id"],
            prop=prop,
            schema=schema,
            value=data["value"],
            dataset=data["dataset"],
            lang=data["lang"] or None,
            original_value=data["original_value"] or None,
            origin=data.get("origin") or None,
            first_seen=data["first_seen"],
            external=data["external"] == "t",
            canonical_id=data["entity_id"],
            last_seen=data["last_seen"],
            id=data.get("id"),
        )


def read_statements(fh: BinaryIO, format: str) -> Generator[Statement, None, None]:
    if format == CSV:
        yield from read_csv_statements(fh)
    elif format == PACK:
        yield from read_pack_statements(fh)
    else:
        yield from read_json_statements(fh)


def read_path_statements(path: Path, format: str) -> Generator[Statement, None, None]:
    if str(path) == "-":
        fh = click.get_binary_stream("stdin")
        yield from read_statements(fh, format=format)
        return
    with open(path, "rb") as fh:
        yield from read_statements(fh, format=format)


def get_statement_writer(fh: BinaryIO, format: str) -> "StatementWriter":
    if format == CSV:
        wrapped = TextIOWrapper(fh, encoding=ENCODING, newline="")
        return CSVStatementWriter(wrapped)
    elif format == PACK:
        wrapped = TextIOWrapper(fh, encoding=ENCODING, newline="")
        return PackStatementWriter(wrapped)
    elif format == JSON:
        return JSONStatementWriter(fh)
    raise RuntimeError(f"Unknown statement format: {format}")


def write_statements(
    fh: BinaryIO, format: str, statements: Iterable[Statement]
) -> None:
    writer = get_statement_writer(fh, format)
    for stmt in statements:
        writer.write(stmt)
    writer.close()


class StatementWriter:
    def write(self, stmt: Statement) -> None:
        raise NotImplementedError()

    def close(self) -> None:
        raise NotImplementedError()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class JSONStatementWriter(StatementWriter):
    def __init__(self, fh: BinaryIO) -> None:
        self.fh = fh

    def write(self, stmt: Statement) -> None:
        data = stmt.to_dict()
        out = orjson.dumps(data, option=orjson.OPT_APPEND_NEWLINE)
        self.fh.write(out)

    def close(self) -> None:
        self.fh.flush()


class CSVStatementWriter(StatementWriter):
    def __init__(self, fh: TextIO) -> None:
        self.fh = fh
        self.writer = csv.writer(self.fh, dialect=csv.unix_dialect)
        self.writer.writerow(CSV_COLUMNS)
        self._batch: list[list[str | None]] = []

    def write(self, stmt: Statement) -> None:
        row = stmt.to_csv_row()
        self._batch.append([row[c] for c in CSV_COLUMNS])
        if len(self._batch) >= CSV_BATCH:
            self.writer.writerows(self._batch)
            self._batch.clear()

    def close(self) -> None:
        if len(self._batch) > 0:
            self.writer.writerows(self._batch)
        self.fh.flush()


class PackStatementWriter(StatementWriter):
    def __init__(self, fh: TextIO) -> None:
        self.fh = fh
        self.writer = csv.writer(
            self.fh,
            dialect=csv.unix_dialect,
            quoting=csv.QUOTE_MINIMAL,
        )
        columns = [
            "entity_id",
            "prop",
            "value",
            "dataset",
            "lang",
            "original_value",
            "origin",
            "external",
            "first_seen",
            "last_seen",
            "id",
        ]
        self.writer.writerow(columns)
        self._batch: dict[str, tuple[str | None, ...]] = {}

    def write(self, stmt: Statement) -> None:
        # HACK: This is very similar to the CSV writer, but at the very inner
        # loop of the application, so we're duplicating code here.
        if stmt.id is None:
            raise RuntimeError("Cannot write pack statement without ID")
        row = (
            stmt.entity_id,
            f"{stmt.schema}:{stmt.prop}",
            stmt.value,
            stmt.dataset,
            stmt.lang,
            stmt.original_value,
            stmt.origin,
            "t" if stmt.external else None,
            stmt.first_seen,
            stmt.last_seen,
            stmt.id,
        )
        self._batch[stmt.id] = row
        if len(self._batch) >= CSV_BATCH:
            self.flush()

    def flush(self) -> None:
        self.writer.writerows(self._batch.values())
        self._batch.clear()

    def close(self) -> None:
        self.flush()
        self.fh.flush()
