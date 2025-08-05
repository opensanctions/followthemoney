import pathlib
from followthemoney import model
from followthemoney import registry


def generate_schemata():
    """Generate the schema documentation."""
    base_path = pathlib.Path(__file__).parent.parent / "docs" / "explorer" / "schemata"
    assert base_path.exists(), f"Base path {base_path} does not exist."
    for name, schema in model.schemata.items():
        schema_path = base_path / f"{name}.md"
        # if not schema_path.exists():
        with open(schema_path, "w", encoding="utf-8") as fh:
            fh.write("---\nhide:\n  - toc\n---\n\n")
            fh.write("{% include 'templates/schema.md' %}\n")


def generate_types():
    """Generate the types documentation."""
    base_path = pathlib.Path(__file__).parent.parent / "docs" / "explorer" / "types"
    assert base_path.exists(), f"Base path {base_path} does not exist."
    for type_ in registry.types:
        type_path = base_path / f"{type_.name}.md"
        if not type_path.exists():
            with open(type_path, "w", encoding="utf-8") as fh:
                fh.write(f"{{% set type = select_type('{type_.name}') %}}\n\n")
                fh.write("{% include 'templates/type.md' %}\n")


if __name__ == "__main__":
    # Generate the schema documentation.
    generate_schemata()

    # Generate the registry documentation.
    generate_types()
