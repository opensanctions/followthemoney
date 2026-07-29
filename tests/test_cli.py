import copy
import yaml
import orjson
from pathlib import Path

from click.testing import CliRunner
from followthemoney.cli.cli import cli

# Ensure all CLI subcommands are registered
import followthemoney.cli.mapping  # noqa: F401
import followthemoney.cli.exports  # noqa: F401
import followthemoney.cli.aggregate  # noqa: F401
import followthemoney.cli.sieve  # noqa: F401
import followthemoney.cli.statement  # noqa: F401

FIXTURES_PATH = Path(__file__).parent / "fixtures"


# --- Core commands ---


def test_dump_model(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["dump-model"])
    assert result.exit_code == 0, result.output
    data = orjson.loads(result.output_bytes)
    assert "schemata" in data
    assert "Person" in data["schemata"]
    assert "properties" in data["schemata"]["Person"]


def test_validate(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    result = cli_runner.invoke(cli, ["validate"], input=entity_jsonl)
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) == 8712
    for line in lines[:5]:
        entity = orjson.loads(line)
        assert "schema" in entity
        assert "properties" in entity


def test_pretty(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    # Use a small slice to avoid huge output
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(cli, ["pretty"], input=first_line)
    assert result.exit_code == 0, result.output
    assert "  " in result.output  # indented


def test_sign(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(cli, ["sign", "-s", "test-key"], input=first_line)
    assert result.exit_code == 0, result.output
    entity = orjson.loads(result.output_bytes.strip())
    # Signed IDs contain a dot separator from namespace application
    assert "." in entity["id"]


# --- Sieve ---


def test_sieve_by_schema(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    result = cli_runner.invoke(cli, ["sieve", "-s", "Ownership"], input=entity_jsonl)
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    # Only Company entities should remain
    assert len(lines) == 5808
    schemas = {orjson.loads(l)["schema"] for l in lines}
    assert schemas == {"Company"}


def test_sieve_by_property(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(cli, ["sieve", "-p", "name"], input=first_line)
    assert result.exit_code == 0, result.output
    entity = orjson.loads(result.output_bytes.strip())
    assert "name" not in entity["properties"]


def test_sieve_by_type(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(cli, ["sieve", "-t", "name"], input=first_line)
    assert result.exit_code == 0, result.output
    entity = orjson.loads(result.output_bytes.strip())
    assert "name" not in entity["properties"]


def test_sieve_by_dataset(cli_runner: CliRunner) -> None:
    entities = [
        {"id": "a1", "schema": "Company", "datasets": ["alpha"], "properties": {"name": ["A Corp"]}},
        {"id": "b1", "schema": "Company", "datasets": ["beta"], "properties": {"name": ["B Corp"]}},
        {"id": "c1", "schema": "Company", "datasets": ["alpha", "beta"], "properties": {"name": ["C Corp"]}},
    ]
    input_data = b"\n".join(orjson.dumps(e) for e in entities) + b"\n"

    # Include only alpha
    result = cli_runner.invoke(cli, ["sieve", "-d", "alpha"], input=input_data)
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    ids = {orjson.loads(l)["id"] for l in lines}
    assert ids == {"a1", "c1"}

    # Union: alpha|beta matches all
    result = cli_runner.invoke(cli, ["sieve", "-d", "alpha|beta"], input=input_data)
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) == 3

    # Subtraction: alpha-beta
    result = cli_runner.invoke(cli, ["sieve", "-d", "alpha-beta"], input=input_data)
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    ids = {orjson.loads(l)["id"] for l in lines}
    assert ids == {"a1"}


# --- Aggregation ---


def test_aggregate(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    result = cli_runner.invoke(cli, ["aggregate"], input=entity_jsonl)
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) == 5607


def test_sorted_aggregate(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    # sorted-aggregate requires input sorted by entity ID
    raw_lines = entity_jsonl.strip().split(b"\n")
    sorted_lines = sorted(raw_lines, key=lambda l: orjson.loads(l)["id"])
    sorted_input = b"\n".join(sorted_lines) + b"\n"
    result = cli_runner.invoke(cli, ["sorted-aggregate"], input=sorted_input)
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) == 5607


def test_aggregate_statements_provenance(
    cli_runner: CliRunner, tmp_path: Path
) -> None:
    # An entity whose values come from two different datasets. Aggregating to the
    # flat form collapses provenance into an entity-level `datasets` list that a
    # statement store can't restore; `-s` keeps the statements so it can.
    from followthemoney.dataset import Dataset
    from followthemoney.statement import CSV, Statement, StatementEntity
    from followthemoney.statement import write_statements

    stmts = [
        Statement(
            entity_id="p1", canonical_id="p1", schema="Person",
            prop="name", value="John Doe", dataset="ds_a",
        ),
        Statement(
            entity_id="p1", canonical_id="p1", schema="Person",
            prop="birthDate", value="1976", dataset="ds_b",
        ),
    ]
    csv_path = tmp_path / "stmts.csv"
    with open(csv_path, "wb") as fh:
        write_statements(fh, CSV, iter(stmts))

    # Reloading happens through a *synthetic* dataset, as nomenklatura's store does
    # when it names the dataset after the input filename.
    synthetic = Dataset.make({"name": "schland"})

    # With -s: statement form, provenance preserved on reload.
    result = cli_runner.invoke(
        cli, ["aggregate-statements", "-i", str(csv_path), "-s"]
    )
    assert result.exit_code == 0, result.output
    data = orjson.loads(result.output_bytes.strip().split(b"\n")[0])
    assert "statements" in data and "properties" not in data
    reloaded = StatementEntity.from_data(synthetic, data)
    assert reloaded.datasets == {"ds_a", "ds_b"}, reloaded.datasets

    # Without -s: flat form, provenance lost on the same reload path.
    flat_result = cli_runner.invoke(
        cli, ["aggregate-statements", "-i", str(csv_path)]
    )
    assert flat_result.exit_code == 0, flat_result.output
    flat = orjson.loads(flat_result.output_bytes.strip().split(b"\n")[0])
    assert "properties" in flat and "statements" not in flat
    flat_reloaded = StatementEntity.from_data(synthetic, flat)
    assert flat_reloaded.datasets == {"schland"}, flat_reloaded.datasets


# --- Mapping ---


LINKS_MAPPING = {
    "test_links": {
        "queries": [
            {
                "csv_url": "/dev/null",
                "entities": {
                    "director": {
                        "schema": "Person",
                        "key": "id",
                        "properties": {"name": {"column": "name"}},
                    },
                    "company": {
                        "schema": "Company",
                        "key": "comp_id",
                        "properties": {"name": {"column": "comp_name"}},
                    },
                    "directorship": {
                        "schema": "Directorship",
                        "keys": ["comp_id", "id"],
                        "properties": {
                            "director": {"entity": "director"},
                            "organization": {"entity": "company"},
                            "role": {"column": "role"},
                        },
                    },
                },
            }
        ]
    }
}


def test_map_csv(cli_runner: CliRunner, tmp_path: Path) -> None:
    csv_data = (FIXTURES_PATH / "links.csv").read_text()
    mapping_path = tmp_path / "mapping.yml"
    mapping_path.write_text(yaml.dump(LINKS_MAPPING))
    result = cli_runner.invoke(
        cli,
        ["map-csv", "--no-sign", str(mapping_path)],
        input=csv_data,
    )
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) == 3
    schemas = {orjson.loads(l)["schema"] for l in lines}
    assert schemas == {"Person", "Company", "Directorship"}
    entities = [orjson.loads(l) for l in lines]
    person = next(e for e in entities if e["schema"] == "Person")
    assert person["properties"]["name"] == ["Wile E. Coyote"]
    company = next(e for e in entities if e["schema"] == "Company")
    assert company["properties"]["name"] == ["ACME Inc."]


def test_map(cli_runner: CliRunner, tmp_path: Path) -> None:
    csv_url = "file://" + str(FIXTURES_PATH / "links.csv")
    mapping = copy.deepcopy(LINKS_MAPPING)
    mapping["test_links"]["queries"][0]["csv_url"] = csv_url
    mapping_path = tmp_path / "mapping.yml"
    mapping_path.write_text(yaml.dump(mapping))
    result = cli_runner.invoke(cli, ["map", "--no-sign", str(mapping_path)])
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) == 3
    schemas = {orjson.loads(l)["schema"] for l in lines}
    assert schemas == {"Person", "Company", "Directorship"}


# --- Exports ---


def test_export_csv(cli_runner: CliRunner, entity_jsonl: bytes, tmp_path: Path) -> None:
    outdir = tmp_path / "csv_out"
    result = cli_runner.invoke(
        cli, ["export-csv", "-o", str(outdir)], input=entity_jsonl
    )
    assert result.exit_code == 0, result.output
    assert (outdir / "Company.csv").exists()
    assert (outdir / "Ownership.csv").exists()
    # Check CSV has content beyond the header
    company_csv = (outdir / "Company.csv").read_text()
    assert len(company_csv.strip().splitlines()) > 1


def test_export_excel(
    cli_runner: CliRunner, entity_jsonl: bytes, tmp_path: Path
) -> None:
    outfile = tmp_path / "out.xlsx"
    result = cli_runner.invoke(
        cli, ["export-excel", "-o", str(outfile)], input=entity_jsonl
    )
    assert result.exit_code == 0, result.output
    assert outfile.exists()
    assert outfile.stat().st_size > 0


def test_export_rdf(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(cli, ["export-rdf"], input=first_line)
    assert result.exit_code == 0, result.output
    assert "rdf-syntax-ns#type" in result.output


def test_export_gexf(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(cli, ["export-gexf"], input=first_line)
    assert result.exit_code == 0, result.output
    assert "<gexf" in result.output


def test_export_cypher(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(cli, ["export-cypher"], input=first_line)
    assert result.exit_code == 0, result.output
    assert "MERGE" in result.output


def test_export_neo4j_bulk(
    cli_runner: CliRunner, entity_jsonl: bytes, tmp_path: Path
) -> None:
    outdir = tmp_path / "neo4j_out"
    result = cli_runner.invoke(
        cli, ["export-neo4j-bulk", "-o", str(outdir)], input=entity_jsonl
    )
    assert result.exit_code == 0, result.output
    # Should have node and relationship CSV files
    files = list(outdir.iterdir())
    assert len(files) > 0


# --- Statements ---


def test_statements(cli_runner: CliRunner, entity_jsonl: bytes) -> None:
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    result = cli_runner.invoke(
        cli,
        ["statements", "-", "-d", "test_ds", "-f", "json"],
        input=first_line,
    )
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) > 0
    stmt = orjson.loads(lines[0])
    assert stmt["dataset"] == "test_ds"


def test_format_statements(
    cli_runner: CliRunner, entity_jsonl: bytes, tmp_path: Path
) -> None:
    # Produce JSON statements first
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    json_out = tmp_path / "stmts.json"
    result = cli_runner.invoke(
        cli,
        ["statements", "-", "-d", "test_ds", "-f", "json", "-o", str(json_out)],
        input=first_line,
    )
    assert result.exit_code == 0, result.output

    # Convert JSON → CSV
    csv_out = tmp_path / "stmts.csv"
    result = cli_runner.invoke(
        cli,
        [
            "format-statements",
            "-i", str(json_out),
            "-f", "json",
            "-x", "csv",
            "-o", str(csv_out),
        ],
    )
    assert result.exit_code == 0, result.output
    csv_content = csv_out.read_text()
    assert "canonical_id" in csv_content  # CSV header
    assert "test_ds" in csv_content


def test_aggregate_statements(
    cli_runner: CliRunner, entity_jsonl: bytes, tmp_path: Path
) -> None:
    # Produce JSON statements
    first_line = entity_jsonl.split(b"\n", 1)[0] + b"\n"
    json_out = tmp_path / "stmts.json"
    result = cli_runner.invoke(
        cli,
        ["statements", "-", "-d", "test_ds", "-f", "json", "-o", str(json_out)],
        input=first_line,
    )
    assert result.exit_code == 0, result.output

    # Aggregate statements back to entities
    result = cli_runner.invoke(
        cli,
        [
            "aggregate-statements",
            "-i", str(json_out),
            "-f", "json",
            "-d", "test_ds",
        ],
    )
    assert result.exit_code == 0, result.output
    lines = result.output_bytes.strip().split(b"\n")
    assert len(lines) == 1
    entity = orjson.loads(lines[0])
    assert entity["schema"] == "Company"
