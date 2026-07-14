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
    # extends lists all ancestors, matching the schema detail view.
    person = next(e for e in data if e["name"] == "Person")
    assert "LegalEntity" in person["extends"]
    assert "Thing" in person["extends"]


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
    # Inherited props (e.g. `name` from Thing) are included in the field list.
    assert "name" in prop_names
    # The schema view is an ultra-short index: name + type only, no qname/schema
    # origin (those live in `ref prop`).
    name_prop = next(p for p in data["properties"] if p["name"] == "name")
    assert name_prop["type"] == "name"
    assert "qname" not in name_prop and "schema" not in name_prop


def test_ref_schema_includes_stubs_with_reverse(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "schema", "Person"])
    props = {p["name"]: p for p in data["properties"]}
    # Stub (reverse-edge) properties are listed and carry the forward qname they
    # reverse, rather than a bare stub flag.
    owner = props["ownershipOwner"]
    assert owner["reverse"] == "Ownership:owner"
    assert "stub" not in owner


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


def test_ref_type_detail_counts_values_and_lists_props(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "types", "topic"])
    assert data["name"] == "topic"
    assert data["enum"] is True
    # The detail view reports a count, not the inlined value set — the full set
    # lives behind `ref type-values topic`.
    assert data["values_count"] > 0
    assert "values" not in data
    assert any(p["name"] == "topics" for p in data["properties"])
    # A non-enum type drops the enum flag (false) and carries no values or count.
    name_type = _json(cli_runner, ["ref", "type", "name"])
    assert "enum" not in name_type
    assert "values" not in name_type
    assert "values_count" not in name_type


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
    # The full value set is deferred to `ref type-values gender`; here we only
    # report how many there are.
    assert data["values_count"] == 3
    assert "values" not in data


def test_ref_json_flag_before_subcommand(cli_runner: CliRunner) -> None:
    # `--json` on the group must reach the subcommand, not be swallowed.
    result = cli_runner.invoke(cli, ["ref", "--json", "type", "country"])
    assert result.exit_code == 0, result.output
    data = orjson.loads(result.output_bytes)
    assert data["name"] == "country"
    assert data["values_count"] > 5


def test_ref_type_values_singular_and_plural(cli_runner: CliRunner) -> None:
    # The command resolves the singular type name and the plural group name.
    singular = _json(cli_runner, ["ref", "type-values", "country"])
    plural = _json(cli_runner, ["ref", "type-values", "countries"])
    assert singular == plural
    assert singular["de"] == "Germany"
    assert len(singular) > 200


def test_ref_types_values_alias(cli_runner: CliRunner) -> None:
    via_type = _json(cli_runner, ["ref", "type-values", "gender"])
    via_types = _json(cli_runner, ["ref", "types-values", "gender"])
    assert via_type == via_types == {"male": "male", "female": "female", "other": "other"}


def test_ref_type_values_non_enum_errors(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["ref", "type-values", "name"])
    assert result.exit_code == 2
    assert "not enumerated" in result.output


def test_ref_type_values_unknown_suggests(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["ref", "type-values", "contry"])
    assert result.exit_code == 2
    assert "Did you mean: country?" in result.output


def test_ref_slim_drops_storage_and_display_keys(cli_runner: CliRunner) -> None:
    schema = _json(cli_runner, ["ref", "schema", "Person"])
    assert "plural" not in schema
    # maxLength is stripped at every depth, including nested property dicts.
    assert all("maxLength" not in p for p in schema["properties"])
    type_ = _json(cli_runner, ["ref", "type", "country"])
    assert "maxLength" not in type_ and "plural" not in type_


def test_ref_schema_view_is_terse(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "schema", "Person"])
    # Top-level noise is trimmed; navigable fields stay.
    for dropped in ("schemata", "caption", "descendants", "required", "temporalExtent"):
        assert dropped not in data
    assert "extends" in data and "featured" in data
    # Properties are name + type only; stubs add a `reverse` qname.
    allowed = {"name", "type", "reverse", "stub"}
    for prop in data["properties"]:
        assert set(prop).issubset(allowed)
        assert "name" in prop and "type" in prop


def test_ref_schema_skips_hidden_and_deprecated(cli_runner: CliRunner) -> None:
    # Hidden and deprecated properties never appear in the schema field list.
    from followthemoney import model

    schema = model.get("Person")
    assert schema is not None
    listed = {p["name"] for p in _json(cli_runner, ["ref", "schema", "Person"])["properties"]}
    for prop in schema.properties.values():
        if prop.hidden or prop.deprecated:
            assert prop.name not in listed


def test_ref_schema_edge_is_boolean(cli_runner: CliRunner) -> None:
    # Edge schemata collapse the edge spec to `edge: true`; non-edges omit it.
    ownership = _json(cli_runner, ["ref", "schema", "Ownership"])
    assert ownership["edge"] is True
    person = _json(cli_runner, ["ref", "schema", "Person"])
    assert "edge" not in person


def test_ref_slim_drops_false_matchable_and_abstract(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "schemata"])
    person = next(e for e in data if e["name"] == "Person")
    # Person is matchable and concrete: matchable stays True, abstract is dropped.
    assert person["matchable"] is True
    assert "abstract" not in person
    # A non-matchable schema drops the matchable key rather than showing false.
    document = next(e for e in data if e["name"] == "Document")
    assert "matchable" not in document


def test_ref_slim_drops_false_enum(cli_runner: CliRunner) -> None:
    # A non-enum type drops `enum` rather than reporting enum: false; the True
    # case still shows on an enum type.
    name_type = _json(cli_runner, ["ref", "type", "name"])
    assert "enum" not in name_type
    country = _json(cli_runner, ["ref", "type", "country"])
    assert country["enum"] is True


def test_ref_slim_drops_label_echoing_name(cli_runner: CliRunner) -> None:
    # Person's label equals its name, so the top-level label is dropped.
    person = _json(cli_runner, ["ref", "schema", "Person"])
    assert person["name"] == "Person"
    assert "label" not in person
    # A label that differs from the name (Title Case) is kept — checked on the
    # prop detail view, which still carries labels.
    name_prop = _json(cli_runner, ["ref", "prop", "Person:name"])
    assert name_prop["label"] == "Name"


def test_ref_types_listing_drops_pivot(cli_runner: CliRunner) -> None:
    data = _json(cli_runner, ["ref", "types"])
    assert all("pivot" not in e for e in data)


def test_ref_type_values_map_not_slimmed(cli_runner: CliRunner) -> None:
    # Raw value maps are emitted verbatim — no key happens to collide, but the
    # contract is that this command returns the unfiltered code->label mapping.
    data = _json(cli_runner, ["ref", "type-values", "country"])
    assert data["no"] == "Norway"
    assert len(data) > 200


def test_ref_prop_unqualified_errors(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["ref", "prop", "name"])
    assert result.exit_code == 2
    assert "qualified" in result.output


def test_ref_prop_unknown_prop_suggests(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["ref", "prop", "Person:nonsense"])
    assert result.exit_code == 2
    assert "no property" in result.output
