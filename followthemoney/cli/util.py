import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO, cast

import click
import orjson
import yaml
from banal import ensure_list, is_listish

from followthemoney.entity import ValueEntity
from followthemoney.export.common import Exporter
from followthemoney.proxy import E, EntityProxy
from followthemoney.util import MEGABYTE, PathLike

MAX_LINE = 200 * MEGABYTE
InPath = click.Path(dir_okay=False, readable=True, path_type=Path, allow_dash=True)
OutPath = click.Path(dir_okay=False, writable=True, path_type=Path, allow_dash=True)


def write_entity(fh: BinaryIO, entity: EntityProxy, statements: bool = False) -> None:
    data = entity.to_statement_dict() if statements else entity.to_dict()
    entity_id = data.pop("id")
    assert entity_id is not None, data
    # Emit `id` as the first key so each JSONL line is byte-sortable by ID
    # with plain `sort`. `ftm sorted-aggregate` depends on this.
    sort_data = {"id": entity_id}
    sort_data.update(data)
    out = orjson.dumps(sort_data, option=orjson.OPT_APPEND_NEWLINE)
    fh.write(out)


def binary_entities(
    fh: BinaryIO, entity_type: type[E], cleaned: bool = True, max_line: int = MAX_LINE
) -> Generator[E, None, None]:
    while line := fh.readline(max_line):
        data = orjson.loads(line)
        yield entity_type.from_dict(data, cleaned=cleaned)


def path_entities(
    path: PathLike,
    entity_type: type[E],
    cleaned: bool = True,
    max_line: int = MAX_LINE,
) -> Generator[E, None, None]:
    with click.open_file(path, "rb") as fh:
        yield from binary_entities(
            cast(BinaryIO, fh), entity_type, cleaned=cleaned, max_line=max_line
        )


@contextmanager
def path_writer(path: PathLike) -> Generator[BinaryIO, None, None]:
    """Open a file for writing binary content, or use stdout."""
    with click.open_file(path, "wb") as fh:
        yield cast(BinaryIO, fh)


def export_stream(exporter: Exporter, path: Path) -> None:
    try:
        for entity in path_entities(path, ValueEntity):
            exporter.write(entity)
    except BrokenPipeError:
        raise click.Abort()
    finally:
        exporter.finalize()


def load_mapping_file(file_path: PathLike) -> Any:
    """Load a YAML (or JSON) bulk load mapping file."""
    file_path = os.path.abspath(file_path)
    with open(file_path, "r") as fh:
        data = yaml.safe_load(fh) or {}
    return resolve_includes(file_path, data)


def resolve_includes(file_path: PathLike, data: Any) -> Any:
    """Handle include statements in the graph configuration file.

    This allows the YAML graph configuration to be broken into
    multiple smaller fragments that are easier to maintain."""
    if is_listish(data):
        return [resolve_includes(file_path, i) for i in data]
    if isinstance(data, dict):
        for include_path in ensure_list(data.pop("include", [])):
            if include_path is None:
                continue
            dir_prefix = os.path.dirname(file_path)
            include_path = os.path.join(dir_prefix, include_path)
            data.update(load_mapping_file(include_path))
        for key, value in data.items():
            data[key] = resolve_includes(file_path, value)
    return data
