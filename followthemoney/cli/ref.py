"""``ftm ref`` — offline, incremental exploration of the FtM model.

This command group exists so a coding agent (or a human) can discover the
schema/type model one small step at a time — what schemata exist, what
properties a ``Person`` accepts, what a property's type is — without reading
the YAML sources or dumping the entire ``model.json``. Unlike a bundled
snapshot, it reads the live in-process ``model`` and ``registry``, so it always
reflects the installed version of followthemoney.

Every command renders a rich table on a terminal and machine-readable JSON when
``--json`` is passed or stdout is piped (see ``followthemoney.cli.render``)."""

import sys
import click
import difflib
from typing import Any, Dict, List, Optional

from followthemoney import model
from followthemoney.types import registry
from followthemoney.types.common import EnumType
from followthemoney.schema import Schema
from followthemoney.property import Property
from followthemoney.cli.cli import cli
from followthemoney.cli.render import (
    is_json_mode,
    emit_json,
    print_markdown,
    print_table,
)

JSON_OPTION = click.option(
    "--json", "json_flag", is_flag=True, default=False, help="Emit JSON output."
)


def _json_mode(ctx: click.Context, json_flag: bool) -> bool:
    """Resolve JSON mode, honouring ``--json`` on either the group or command.

    ``--json`` may be supplied before the subcommand (``ftm ref --json type X``)
    or after it (``ftm ref type X --json``). The group stashes its flag in
    ``ctx.obj`` so subcommands can OR the two together."""
    inherited = bool(ctx.obj) and bool(ctx.obj.get("json"))
    return is_json_mode(json_flag or inherited)


def _suggest(name: str, valid: List[str]) -> Optional[str]:
    """Return the closest valid name to ``name``, or ``None`` if none is close."""
    matches = difflib.get_close_matches(name, valid, n=1, cutoff=0.6)
    return matches[0] if matches else None


def _fail(message: str, suggestion: Optional[str] = None) -> None:
    """Print a usage error (with an optional did-you-mean) and exit code 2."""
    hint = f" Did you mean: {suggestion}?" if suggestion else ""
    click.echo(f"error: {message}{hint}", err=True)
    sys.exit(2)


def _schema_flags(schema: Schema) -> str:
    """Compact flag string for a schema row (abstract/hidden/edge/...)."""
    flags = []
    if schema.abstract:
        flags.append("abstract")
    if schema.hidden:
        flags.append("hidden")
    if schema.generated:
        flags.append("generated")
    if schema.edge:
        flags.append("edge")
    if schema.deprecated:
        flags.append("deprecated")
    return ", ".join(flags)


def _prop_flags(prop: Property) -> str:
    """Compact flag string for a property row (stub/hidden/deprecated)."""
    flags = []
    if prop.stub:
        flags.append("stub")
    if prop.hidden:
        flags.append("hidden")
    if prop.deprecated:
        flags.append("deprecated")
    return ", ".join(flags)


def _prop_payload(prop: Property) -> Dict[str, Any]:
    """JSON shape for a property within a schema listing: to_dict + origin schema."""
    data: Dict[str, Any] = dict(prop.to_dict())
    data["schema"] = prop.schema.name
    return data


@cli.group("ref", invoke_without_command=True, help="Browse the FtM model offline.")
@JSON_OPTION
@click.pass_context
def ref(ctx: click.Context, json_flag: bool) -> None:
    """Show a model overview when invoked without a subcommand."""
    ctx.ensure_object(dict)["json"] = json_flag
    if ctx.invoked_subcommand is not None:
        return
    schemata = sorted(model.schemata.keys())
    types = sorted(t.name for t in registry.types)
    commands = [
        ("schemata", "List all schemata."),
        ("schema NAME", "Show one schema and all its properties."),
        ("types [NAME]", "List property types, or detail one."),
        ("type NAME", "Detail one property type (alias)."),
        ("prop QNAME", "Show one property, e.g. Person:name."),
    ]
    if _json_mode(ctx, json_flag):
        emit_json(
            {
                "schemata_count": len(schemata),
                "types_count": len(types),
                "commands": [{"command": c, "help": h} for c, h in commands],
            }
        )
        return
    click.echo(f"FtM model: {len(schemata)} schemata, {len(types)} property types\n")
    rows = [[f"ftm ref {cmd}", help_] for cmd, help_ in commands]
    print_table(rows, headers=["command", "description"], title="ftm ref")


@ref.command("schemata", help="List all schemata in the model.")
@click.option("--matchable", is_flag=True, help="Only matchable schemata.")
@click.option(
    "--abstract/--no-abstract", default=None, help="Filter by abstract flag."
)
@JSON_OPTION
@click.pass_context
def ref_schemata(
    ctx: click.Context, matchable: bool, abstract: Optional[bool], json_flag: bool
) -> None:
    """List schemata with their key attributes."""
    entries: List[Dict[str, Any]] = []
    for name in sorted(model.schemata.keys()):
        schema = model.schemata[name]
        if matchable and not schema.matchable:
            continue
        if abstract is not None and schema.abstract != abstract:
            continue
        entries.append(
            {
                "name": name,
                "label": schema.label,
                "matchable": schema.matchable,
                "abstract": schema.abstract,
                "extends": sorted(s.name for s in schema.extends),
                "description": (schema.description or "").strip(),
            }
        )

    if _json_mode(ctx, json_flag):
        emit_json(entries)
        return
    rows = [
        [
            e["name"],
            "✓" if e["matchable"] else "",
            _schema_flags(model.schemata[e["name"]]),
            ", ".join(e["extends"]),
            e["description"],
        ]
        for e in entries
    ]
    print_table(
        rows,
        headers=["schema", "matchable", "flags", "extends", "description"],
        caption=f"{len(entries)} schema(s)",
    )


@ref.command("schema", help="Show one schema and all its (inherited) properties.")
@click.argument("name")
@click.option("--stubs", is_flag=True, help="Include stub (reverse-edge) properties.")
@JSON_OPTION
@click.pass_context
def ref_schema(ctx: click.Context, name: str, stubs: bool, json_flag: bool) -> None:
    """Show a schema's metadata plus the full property set (own + inherited)."""
    schema = model.get(name)
    if schema is None:
        _fail(
            f"Unknown schema {name!r}.",
            _suggest(name, list(model.schemata.keys())),
        )
        return

    props = [p for p in schema.sorted_properties if stubs or not p.stub]
    # Start from the model's own serialization so new schema fields flow through
    # automatically; override the few views `ref` presents differently.
    extends = sorted(s.name for s in schema.schemata if s != schema)
    summary: Dict[str, Any] = dict(schema.to_dict())
    summary["name"] = schema.name
    summary["extends"] = extends  # all ancestors, not just direct parents
    summary["descendants"] = sorted(s.name for s in schema.descendants)
    summary["properties"] = [_prop_payload(p) for p in props]

    if _json_mode(ctx, json_flag):
        emit_json(summary)
        return

    click.echo(f"{schema.name}  ({schema.label})")
    if schema.description:
        print_markdown(schema.description.strip())
    click.echo("")
    click.echo(f"  matchable:    {'yes' if schema.matchable else 'no'}")
    click.echo(f"  extends:      {', '.join(extends) or '(none)'}")
    click.echo(f"  featured:     {', '.join(schema.featured) or '(none)'}")
    click.echo(f"  required:     {', '.join(schema.required) or '(none)'}")
    click.echo("")
    rows = [
        [
            p.name,
            p.type.name,
            "✓" if p.matchable else "",
            _prop_flags(p),
            p.schema.name,
            (p.description or "").strip(),
        ]
        for p in props
    ]
    print_table(
        rows,
        headers=["property", "type", "matchable", "flags", "schema", "description"],
        caption=f"{len(props)} property/properties (own + inherited)",
    )


def _type_detail(ctx: click.Context, name: str, json_flag: bool) -> None:
    """Render the detail view for a single property type."""
    try:
        type_ = registry.get(name)
    except AttributeError:
        type_ = None
    if type_ is None:
        _fail(
            f"Unknown type {name!r}.",
            _suggest(name, [t.name for t in registry.types]),
        )
        return

    is_enum = isinstance(type_, EnumType)
    using = sorted(
        (
            {"qname": p.qname, "schema": p.schema.name, "name": p.name}
            for p in model.properties
            if p.type == type_
        ),
        key=lambda p: p["qname"],
    )
    # to_dict() omits the type's own name; carry it so the payload self-identifies.
    data: Dict[str, Any] = dict(type_.to_dict())
    data["name"] = type_.name
    data["enum"] = is_enum
    data["properties"] = using

    if _json_mode(ctx, json_flag):
        emit_json(data)
        return

    click.echo(f"{type_.name}  ({type_.label})")
    if type_.docs:
        print_markdown(type_.docs)
    click.echo("")
    click.echo(f"  matchable:  {'yes' if type_.matchable else 'no'}")
    click.echo(f"  pivot:      {'yes' if type_.pivot else 'no'}")
    click.echo(f"  enum:       {'yes' if is_enum else 'no'}")
    click.echo(f"  group:      {type_.group or '(none)'}")
    click.echo("")

    prop_rows = [[p["qname"], p["schema"]] for p in using]
    print_table(
        prop_rows,
        headers=["property", "schema"],
        caption=f"{len(using)} property/properties of type {type_.name!r}",
    )

    if isinstance(type_, EnumType):
        click.echo("")
        values = type_.names
        rows = [[code, label] for code, label in sorted(values.items())]
        print_table(
            rows, headers=["value", "label"], caption=f"{len(values)} supported value(s)"
        )


@ref.command("types", help="List property types, or detail one with [NAME].")
@click.argument("name", required=False)
@JSON_OPTION
@click.pass_context
def ref_types(ctx: click.Context, name: Optional[str], json_flag: bool) -> None:
    """List all property types, or show one type's detail when NAME is given."""
    if name is not None:
        _type_detail(ctx, name, json_flag)
        return

    entries: List[Dict[str, Any]] = []
    for type_ in sorted(registry.types, key=lambda t: t.name):
        values = type_.names if isinstance(type_, EnumType) else {}
        entry: Dict[str, Any] = {
            "name": type_.name,
            "label": type_.label,
            "matchable": type_.matchable,
            "pivot": type_.pivot,
            "group": type_.group,
            "values_count": len(values),
        }
        # Elide enum values from the index unless there are few enough to scan.
        if 0 < len(values) <= 5:
            entry["values"] = dict(values)
        entries.append(entry)

    if _json_mode(ctx, json_flag):
        emit_json(entries)
        return
    rows = []
    for e in entries:
        if "values" in e:
            values_cell = ", ".join(sorted(e["values"].keys()))
        elif e["values_count"]:
            values_cell = f"{e['values_count']} values"
        else:
            values_cell = ""
        rows.append(
            [
                e["name"],
                e["group"] or "",
                "✓" if e["matchable"] else "",
                "✓" if e["pivot"] else "",
                values_cell,
            ]
        )
    print_table(
        rows,
        headers=["type", "group", "matchable", "pivot", "values"],
        caption=f"{len(entries)} type(s)",
    )


@ref.command("type", help="Detail one property type (alias for `types NAME`).")
@click.argument("name")
@JSON_OPTION
@click.pass_context
def ref_type(ctx: click.Context, name: str, json_flag: bool) -> None:
    """Show one property type's detail; alias of ``ref types NAME``."""
    _type_detail(ctx, name, json_flag)


@ref.command("prop", help="Show one property by qualified name, e.g. Person:name.")
@click.argument("qname")
@JSON_OPTION
@click.pass_context
def ref_prop(ctx: click.Context, qname: str, json_flag: bool) -> None:
    """Show a single property's full definition."""
    if ":" not in qname:
        _fail(f"Property name must be qualified as Schema:prop; got {qname!r}.")
        return
    # Resolve via the schema's property set rather than the qname index, so an
    # inherited property addressed on a child schema (`Person:name`, where the
    # canonical qname is `Thing:name`) still resolves to the defining property.
    schema_name, _, prop_name = qname.partition(":")
    schema = model.get(schema_name)
    if schema is None:
        _fail(
            f"Unknown schema {schema_name!r} in {qname!r}.",
            _suggest(schema_name, list(model.schemata.keys())),
        )
        return
    prop = schema.get(prop_name)
    if prop is None:
        _fail(
            f"Schema {schema_name!r} has no property {prop_name!r}.",
            _suggest(prop_name, list(schema.properties.keys())),
        )
        return

    schemata = sorted(s.name for s in model if s.get(prop.name) == prop)
    data: Dict[str, Any] = dict(prop.to_dict())
    data["schemata"] = schemata
    if isinstance(prop.type, EnumType):
        data["values"] = dict(prop.type.names)

    if _json_mode(ctx, json_flag):
        emit_json(data)
        return

    click.echo(f"{prop.qname}  ({prop.label})")
    if prop.description:
        print_markdown(prop.description.strip())
    click.echo("")
    click.echo(f"  type:       {prop.type.name}")
    click.echo(f"  matchable:  {'yes' if prop.matchable else 'no'}")
    if prop.range is not None:
        click.echo(f"  range:      {prop.range.name}")
    if prop.reverse is not None:
        click.echo(f"  reverse:    {prop.reverse.qname}")
    if prop.format is not None:
        click.echo(f"  format:     {prop.format}")
    click.echo(f"  maxLength:  {prop.max_length}")
    if prop.stub:
        click.echo("  stub:       yes (reverse edge, not writable)")
    if prop.deprecated:
        click.echo("  deprecated: yes")
    if prop.examples:
        click.echo(f"  examples:   {', '.join(prop.examples)}")
    click.echo(f"  schemata:   {', '.join(schemata)}")
    if isinstance(prop.type, EnumType):
        click.echo("")
        rows = [[code, label] for code, label in sorted(prop.type.names.items())]
        print_table(
            rows,
            headers=["value", "label"],
            caption=f"{len(prop.type.names)} value(s) for type {prop.type.name!r}",
        )
