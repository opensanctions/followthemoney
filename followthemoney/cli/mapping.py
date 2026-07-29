import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TextIO

import click
from banal import keys_values

from followthemoney import model
from followthemoney.cli.cli import cli
from followthemoney.cli.util import (
    InPath,
    OutPath,
    load_mapping_file,
    path_writer,
    write_entity,
)
from followthemoney.mapping.csv import CSVSource
from followthemoney.mapping.query import QueryMapping
from followthemoney.namespace import Namespace


@contextmanager
def input_file(path: Path) -> Generator[TextIO, None, None]:
    if str(path) == "-":
        yield sys.stdin
        return
    with open(path, "r") as fh:
        yield fh


@cli.command("map", help="Execute a mapping file and emit objects")
@click.option("-o", "--outfile", type=OutPath, default="-")
@click.option("-d", "--dataset", type=str, default=None, help="Dataset name")
@click.option(
    "--sign/--no-sign",
    is_flag=True,
    default=True,
    help="Apply HMAC signature",
)
@click.argument("mapping_yaml", type=click.Path(exists=True, path_type=Path))
def run_mapping(
    outfile: Path, mapping_yaml: Path, dataset: str | None, sign: bool = True
) -> None:
    config = load_mapping_file(mapping_yaml)
    try:
        with path_writer(outfile) as outfh:
            for config_dataset, meta in config.items():
                ds = dataset or config_dataset
                ns = Namespace(ds)
                for mapping in keys_values(meta, "queries", "query"):
                    entities = model.map_entities(
                        mapping, key_prefix=ds, dataset=ds
                    )
                    for entity in entities:
                        if sign:
                            entity = ns.apply(entity)
                        write_entity(outfh, entity)
    except BrokenPipeError:
        raise click.Abort()
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc))


@cli.command("map-csv", help="Map CSV data from stdin and emit objects")
@click.option("-i", "--infile", type=InPath, default="-")
@click.option("-o", "--outfile", type=OutPath, default="-")
@click.option("-d", "--dataset", type=str, default=None, help="Dataset name")
@click.option(
    "--sign/--no-sign", is_flag=True, default=True, help="Apply HMAC signature"
)
@click.argument("mapping_yaml", type=click.Path(exists=True, path_type=Path))
def stream_mapping(
    infile: Path, outfile: Path, mapping_yaml: Path, dataset: str | None, sign: bool = True
) -> None:
    queries: list[tuple[str, QueryMapping, CSVSource]] = []
    config = load_mapping_file(mapping_yaml)
    for config_dataset, meta in config.items():
        ds = dataset or config_dataset
        for data in keys_values(meta, "queries", "query"):
            data.pop("database", None)
            data["csv_url"] = "/dev/null"
            query = model.make_mapping(data, key_prefix=ds, dataset=ds)
            source = query.source
            assert isinstance(source, CSVSource)
            queries.append((ds, query, source))

    try:
        with path_writer(outfile) as outfh, input_file(infile) as fh:
            for record in CSVSource.read_csv(fh):
                for dataset, query, source in queries:
                    ns = Namespace(dataset)
                    if source.check_filters(record):
                        entities = query.map(record)
                        for entity in entities.values():
                            if sign:
                                entity = ns.apply(entity)
                            write_entity(outfh, entity)
    except BrokenPipeError:
        raise click.Abort()
