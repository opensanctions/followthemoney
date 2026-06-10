import orjson
from click.testing import CliRunner

from followthemoney.cli.cli import cli

# Importing the module registers the `ref` group on the root CLI.
import followthemoney.cli.ref as refmod  # noqa: F401


def _json(cli_runner: CliRunner, args: list[str]):
    """Invoke a ref command in --json mode and parse the payload."""
    result = cli_runner.invoke(cli, [*args, "--json"])
    assert result.exit_code == 0, result.output
    return orjson.loads(result.output_bytes)


def test_ref_overview(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref"])
    assert data["schemata_count"] > 50
    assert data["types_count"] > 10
    assert any(c["command"].startswith("schema") for c in data["commands"])


def test_ref_schemata_list(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "schemata"])
    names = {e["name"] for e in data}
    assert "Person" in names
    assert "Thing" in names


def test_ref_schemata_matchable_filter(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "schemata", "--matchable"])
    assert all(e["matchable"] for e in data)
    assert "Person" in {e["name"] for e in data}


def test_ref_schema_includes_inherited(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "schema", "Person"])
    assert data["name"] == "Person"
    # extends lists ALL ancestors, not just the direct parent.
    assert "LegalEntity" in data["extends"]
    assert "Thing" in data["extends"]
    assert "Person" not in data["extends"]
    prop_names = {p["name"] for p in data["properties"]}
    # `name` is inherited from Thing; it must appear with its origin schema.
    assert "name" in prop_names
    name_prop = next(p for p in data["properties"] if p["name"] == "name")
    assert name_prop["from_schema"] == "Thing"


def test_ref_schema_hides_stubs_by_default(cli_runner: CliRunner) -> None:
    default = _json(cli_runner, ["ref", "schema", "Person"])
    with_stubs = _json(cli_runner, ["ref", "schema", "Person", "--stubs"])
    assert not any(p.get("stub") for p in default["properties"])
    assert len(with_stubs["properties"]) >= len(default["properties"])


def test_ref_schema_unknown_suggests(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["ref", "schema", "Persn"])
    assert result.exit_code == 2
    assert "Did you mean: Person?" in result.output


def test_ref_types_list_elides_large_enums(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "types"])
    by_name = {e["name"] for e in data}
    assert "name" in by_name and "country" in by_name
    country = next(e for e in data if e["name"] == "country")
    # Large enums are counted but their values are omitted from the index.
    assert country["values_count"] > 5
    assert "values" not in country
    gender = next(e for e in data if e["name"] == "gender")
    assert gender["values_count"] <= 5
    assert "values" in gender


def test_ref_type_detail_has_values_and_props(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "types", "topic"])
    assert data["name"] == "topic"
    assert len(data["values"]) > 0
    assert any(p["name"] == "topics" for p in data["properties"])


def test_ref_type_singular_alias(cli_runner: CliRunner) -> None:
    plural = _json(cli_runner, ["ref", "types", "gender"])
    singular = _json(cli_runner, ["ref", "type", "gender"])
    assert plural == singular


def test_ref_prop_resolves_inherited(cli_runner: CliRunner) -> None:
    # Addressed on Person, but the property is defined on Thing.
    data = _json(cli_runner, ["ref", "prop", "Person:name"])
    assert data["qname"] == "Thing:name"
    assert "Person" in data["schemata"]


def test_ref_prop_enum_values(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "prop", "Person:gender"])
    assert data["type"] == "gender"
    assert "male" in data["values"]


def test_ref_json_flag_before_subcommand(cli_runner: CliRunner) -> None:
    # `--json` on the group must reach the subcommand, not be swallowed.
    result = cli_runner.invoke(cli, ["ref", "--json", "type", "country"])
    assert result.exit_code == 0, result.output
    data = orjson.loads(result.output_bytes)
    assert data["name"] == "country"
    assert len(data["values"]) > 5


def test_ref_prop_unqualified_errors(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["ref", "prop", "name"])
    assert result.exit_code == 2
    assert "qualified" in result.output


def test_ref_prop_unknown_prop_suggests(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["ref", "prop", "Person:nonsense"])
    assert result.exit_code == 2
    assert "no property" in result.output
