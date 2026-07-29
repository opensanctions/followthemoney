import click
from pathlib import Path
from collections.abc import Iterable

from followthemoney import model
from followthemoney.entity import ValueEntity
from followthemoney.types import registry
from followthemoney.dataset.parse import parse_query
from followthemoney.dataset.query import DatasetQuery, match_datasets
from followthemoney.cli.cli import cli
from followthemoney.cli.util import InPath, OutPath, path_entities
from followthemoney.cli.util import path_writer, write_entity


def sieve_entity(
    entity: ValueEntity,
    schemata: Iterable[str],
    properties: Iterable[str],
    types: Iterable[str],
    dataset_query: DatasetQuery | None = None,
) -> ValueEntity | None:
    if dataset_query is not None:
        if not match_datasets(dataset_query, entity.datasets):
            return None
    for schema in schemata:
        if entity.schema.is_a(schema):
            return None
    for prop in entity.iterprops():
        if prop.name in properties or prop.qname in properties:
            entity.pop(prop, quiet=True)
        elif prop.type.name in types:
            entity.pop(prop, quiet=True)
    return entity


@cli.command("sieve", help="Filter out parts of entities.")
@click.option("-i", "--infile", type=InPath, default="-")
@click.option("-o", "--outfile", type=OutPath, default="-")
@click.option(
    "-s",
    "--schema",
    type=click.Choice(list(model.schemata.keys())),
    multiple=True,
    help="Filter out the given schemata.",
)
@click.option(
    "-p",
    "--property",
    multiple=True,
    help="Filter out the given property names.",
)
@click.option(
    "-t",
    "--type",
    type=click.Choice([t.name for t in registry.types]),
    multiple=True,
    help="Filter out the given property types.",
)
@click.option(
    "-d",
    "--datasets",
    type=str,
    default=None,
    help="Keep only entities matching a dataset query (e.g. 'a|b', 'a-b').",
)
def sieve(
    infile: Path,
    outfile: Path,
    schema: Iterable[str],
    property: Iterable[str],
    type: Iterable[str],
    datasets: str | None,
) -> None:
    dataset_query: DatasetQuery | None = None
    if datasets is not None:
        dataset_query = parse_query(datasets)
    try:
        with path_writer(outfile) as outfh:
            for entity in path_entities(infile, ValueEntity):
                sieved = sieve_entity(
                    entity, schema, property, type, dataset_query
                )
                if sieved is not None:
                    write_entity(outfh, sieved)
    except BrokenPipeError:
        raise click.Abort()
