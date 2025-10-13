from rigour.names import NameTypeTag

from followthemoney import model
from followthemoney.names import schema_type_tag
from followthemoney.schema import Schema


def req(name: str) -> Schema:
    schema = model.get(name)
    assert schema is not None, f"Schema {name} not found"
    return schema


def test_schema_type_tag():
    assert schema_type_tag(req("Person")) == NameTypeTag.PER
    assert schema_type_tag(req("Organization")) == NameTypeTag.ORG
    assert schema_type_tag(req("Company")) == NameTypeTag.ORG
    assert schema_type_tag(req("LegalEntity")) == NameTypeTag.ENT
    assert schema_type_tag(req("Vessel")) == NameTypeTag.OBJ
    assert schema_type_tag(req("Security")) == NameTypeTag.OBJ
    assert schema_type_tag(req("Airplane")) == NameTypeTag.OBJ
    assert schema_type_tag(req("Interval")) == NameTypeTag.UNK
