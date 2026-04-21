from rigour.names import NamePartTag, NameTypeTag

from followthemoney import model
from followthemoney.dataset.dataset import Dataset
from followthemoney.entity import ValueEntity
from followthemoney.names import PART_TAG_PROPS, entity_names, schema_type_tag
from followthemoney.schema import Schema
from followthemoney.statement.entity import StatementEntity


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


def test_part_tag_props_shape():
    tags_by_prop = dict(PART_TAG_PROPS)
    assert tags_by_prop["firstName"] == (NamePartTag.GIVEN,)
    assert tags_by_prop["lastName"] == (NamePartTag.FAMILY,)
    assert tags_by_prop["secondName"] == (NamePartTag.MIDDLE,)
    assert tags_by_prop["middleName"] == (NamePartTag.MIDDLE,)
    assert tags_by_prop["fatherName"] == (NamePartTag.MIDDLE, NamePartTag.FAMILY)
    assert tags_by_prop["motherName"] == (NamePartTag.MIDDLE, NamePartTag.FAMILY)
    assert tags_by_prop["weakAlias"] == (NamePartTag.NICK,)


def _forms(names: set) -> set:
    return {name.form for name in names}


def test_entity_names_person_basic():
    entity = ValueEntity.from_dict(
        {
            "id": "person-basic",
            "schema": "Person",
            "properties": {
                "name": ["John Smith"],
                "firstName": ["John"],
                "lastName": ["Smith"],
            },
        }
    )
    names = entity_names(entity)
    assert len(names) == 1
    name = next(iter(names))
    assert name.tag == NameTypeTag.PER
    part_tags = {part.form: part.tag for part in name.parts}
    assert part_tags.get("john") == NamePartTag.GIVEN
    assert part_tags.get("smith") == NamePartTag.FAMILY


def test_entity_names_weak_alias_standalone_by_default():
    entity = ValueEntity.from_dict(
        {
            "id": "person-weakalias",
            "schema": "Person",
            "properties": {
                "name": ["John Smith"],
                "weakAlias": ["Johnny"],
            },
        }
    )
    names = entity_names(entity, matchable=False)
    forms = _forms(names)
    assert "john smith" in forms
    assert "johnny" in forms


def test_entity_names_weak_alias_excluded_when_matchable():
    entity = ValueEntity.from_dict(
        {
            "id": "person-weakalias-strict",
            "schema": "Person",
            "properties": {
                "name": ["John Smith"],
                "weakAlias": ["Johnny"],
            },
        }
    )
    names = entity_names(entity, matchable=True)
    forms = _forms(names)
    assert "john smith" in forms
    assert "johnny" not in forms


def test_entity_names_abbreviation_standalone_by_default():
    entity = ValueEntity.from_dict(
        {
            "id": "company-abbrev",
            "schema": "Company",
            "properties": {
                "name": ["International Business Machines"],
                "abbreviation": ["IBM"],
            },
        }
    )
    names = entity_names(entity, matchable=False)
    forms = _forms(names)
    assert any("international" in f for f in forms)
    assert "ibm" in forms

    strict = entity_names(entity, matchable=True)
    strict_forms = _forms(strict)
    assert "ibm" not in strict_forms


def test_entity_names_explicit_props():
    entity = ValueEntity.from_dict(
        {
            "id": "person-explicit-props",
            "schema": "Person",
            "properties": {
                "name": ["John Smith"],
                "alias": ["Johnny S"],
                "firstName": ["John"],
            },
        }
    )
    names = entity_names(entity, props=("name",))
    forms = _forms(names)
    assert "john smith" in forms
    assert "johnny s" not in forms
    # PART_TAG_PROPS still runs — firstName annotates "john" as GIVEN.
    main = next(n for n in names if n.form == "john smith")
    part_tags = {part.form: part.tag for part in main.parts}
    assert part_tags.get("john") == NamePartTag.GIVEN


def test_entity_names_value_matches_statement():
    data = {
        "id": "person-cross",
        "schema": "Person",
        "properties": {
            "name": ["John Smith"],
            "firstName": ["John"],
            "lastName": ["Smith"],
            "weakAlias": ["Johnny"],
        },
    }
    ds = Dataset({"name": "test", "title": "Test"})
    value_names = entity_names(ValueEntity.from_dict(data))
    statement_names = entity_names(StatementEntity.from_data(ds, data))
    assert _forms(value_names) == _forms(statement_names)


def test_entity_names_father_name_does_not_crash():
    # Multi-tag fanout: fatherName emits both MIDDLE and FAMILY for
    # the same string. Ensure this produces a valid result set; the
    # exact per-part tag outcome is a rigour-side concern.
    entity = ValueEntity.from_dict(
        {
            "id": "person-patronymic",
            "schema": "Person",
            "properties": {
                "name": ["Ivan Ivanov Petrov"],
                "firstName": ["Ivan"],
                "fatherName": ["Ivanov"],
                "lastName": ["Petrov"],
            },
        }
    )
    names = entity_names(entity)
    assert len(names) >= 1
    main = next(iter(names))
    assert "ivanov" in {part.form for part in main.parts}
