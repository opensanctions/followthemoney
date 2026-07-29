from collections.abc import Generator
from pathlib import Path

import click

from followthemoney.cli.cli import cli
from followthemoney.cli.util import (
    InPath,
    OutPath,
    path_entities,
    path_writer,
    write_entity,
)
from followthemoney.dataset import Dataset, UndefinedDataset
from followthemoney.statement import (
    CSV,
    FORMATS,
    Statement,
    StatementEntity,
    read_path_statements,
    write_statements,
)


@cli.command("statements", help="Export entities to statements")
@click.argument("path", type=InPath)
@click.option("-o", "--outpath", type=OutPath, default="-")
@click.option("-d", "--dataset", type=str)
@click.option("-f", "--format", type=click.Choice(FORMATS), default=CSV)
def entity_statements(
    path: Path, outpath: Path, dataset: str | None, format: str
) -> None:
    def make_statements() -> Generator[Statement, None, None]:
        dataset_ = dataset or Dataset.UNDEFINED
        for entity in path_entities(path, StatementEntity):
            for stmt in Statement.from_entity(entity, dataset=dataset_):
                if dataset is not None:
                    stmt = stmt.clone(dataset=dataset)
                yield stmt

    with path_writer(outpath) as outfh:
        write_statements(outfh, format, make_statements())


@cli.command("format-statements", help="Convert entity data formats")
@click.option("-i", "--infile", type=InPath, default="-")
@click.option("-o", "--outpath", type=OutPath, default="-")
@click.option("-f", "--in-format", type=click.Choice(FORMATS), default=CSV)
@click.option("-x", "--out-format", type=click.Choice(FORMATS), default=CSV)
def format_statements(
    infile: Path, outpath: Path, in_format: str, out_format: str
) -> None:
    statements = read_path_statements(infile, format=in_format)
    with path_writer(outpath) as outfh:
        write_statements(outfh, out_format, statements)


@cli.command("aggregate-statements", help="Roll up statements into entities")
@click.option("-i", "--infile", type=InPath, default="-")
@click.option("-o", "--outpath", type=OutPath, default="-")
@click.option("-d", "--dataset", type=str, default=UndefinedDataset.name)
@click.option("-f", "--format", type=click.Choice(FORMATS), default=CSV)
@click.option(
    "-s",
    "--statements",
    is_flag=True,
    default=False,
    help="Emit entities with their statements, preserving per-dataset provenance.",
)
def statements_aggregate(
    infile: Path, outpath: Path, dataset: str, format: str, statements: bool
) -> None:
    dataset_ = Dataset.make({"name": dataset})
    with path_writer(outpath) as outfh:
        group: list[Statement] = []
        for stmt in read_path_statements(infile, format=format):
            if len(group) and group[0].canonical_id != stmt.canonical_id:
                entity = StatementEntity.from_statements(dataset_, group)
                write_entity(outfh, entity, statements=statements)
                group = []
            group.append(stmt)
        if len(group) > 0:
            entity = StatementEntity.from_statements(dataset_, group)
            write_entity(outfh, entity, statements=statements)
