import pytest
from rigour.time import utc_now, datetime_iso

from followthemoney.statement.util import BASE_ID
from followthemoney.types import registry
from followthemoney.proxy import EntityProxy
from followthemoney.exc import InvalidData
from followthemoney.dataset import Dataset
from followthemoney.statement import StatementEntity, Statement

DAIMLER = "66ce9f62af8c7d329506da41cb7c36ba058b3d28"
EXAMPLE = {
    "id": "bla",
    "schema": "Person",
    "properties": {"name": ["John Doe"], "lastName": ["Doe"], "birthDate": ["1976"]},
}

EXAMPLE_2 = {
    "id": "test",
    "schema": "Person",
    "properties": {
        "name": ["Ralph Tester"],
        "birthDate": ["1972-05-01"],
        "idNumber": ["9177171", "8e839023"],
        "website": ["https://ralphtester.me"],
        "phone": ["+12025557612"],
        "email": ["info@ralphtester.me"],
        "topics": ["role.spy"],
    },
}


def test_import_entity():
    dx = Dataset.make({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(dx, EXAMPLE_2)
    assert sp.schema is not None
    assert sp.schema.name == "Person"
    assert sp.id == "test"
    assert len(list(sp.statements)) == 9


def test_parse_proxy():
    sp = EntityProxy.from_dict(EXAMPLE_2)
    for stmt in Statement.from_entity(sp, dataset="test", origin="space"):
        assert stmt.entity_id == "test"
        assert stmt.schema == "Person"
        assert stmt.dataset == "test"
        assert stmt.origin == "space"
        if stmt.prop == BASE_ID:
            continue
        assert stmt.prop in sp.schema.properties
        assert stmt.value in sp.get(stmt.prop)

    with pytest.raises(InvalidData):
        EntityProxy.from_dict({"id": "test", "schema": "Banana"})


def test_example_entity():
    dx = Dataset.make({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(dx, EXAMPLE)
    assert len(sp) == 4
    idstmt = list(sp.statements)[-1]
    assert idstmt.value == "c23bd2254b243c438a12525f7d1ab8f8887927d8"
    assert sp.caption == "John Doe"
    assert sp.checksum == "f76794ed2492edda96ca21c1e831dba39b99ffd4"
    assert sp.key_prefix == dx.name
    assert "John Doe", sp.get_type_values(registry.name)
    assert len(list(sp.iterprops())) == 3
    assert len(sp.properties) == 3
    sp.add("country", "us")
    assert len(sp) == 5
    idstmt = list(sp.statements)[-1]
    assert idstmt.value == "5f88a482d141d99c1b749f80cfbb3a038d743d50"
    sp.add("country", {"gb"})
    assert len(sp) == 6
    sp.add("country", ("gb", "us"))
    assert len(sp) == 6
    sp.add("country", ["gb", "us"])
    assert len(sp) == 6
    sp.set("country", "gb")
    assert len(sp) == 5
    assert len(list(sp.iterprops())) == 4
    data = sp.to_dict()
    assert data["id"] == sp.id, data
    idstmt = list(sp.statements)[-1]
    so = sp.clone()
    assert so.id == sp.id
    assert sp.checksum == so.checksum
    assert so.dataset == sp.dataset
    idstmt2 = list(so.statements)[-1]
    assert idstmt.value == idstmt2.value

    sx = StatementEntity.from_statements(dx, sp.statements)
    assert sx.id == sp.id
    assert len(sx) == len(sp)

    sp.add("notes", "Ich bin eine banane!", lang="deu")
    claim = sp.get_statements("notes")[0]
    assert claim.lang == "deu", claim

    sp.add("banana", "Ich bin eine banane!", lang="deu", quiet=True)

    assert len(sp.get_statements("notes")) == 1
    sp.add("notes", None, lang="deu", quiet=True)
    assert len(sp.get_statements("notes")) == 1

    sp.add("alias", "Banana Boy")
    assert len(sp.get_statements("alias")) == 1

    with pytest.raises(InvalidData):
        sp.get_statements("banana")
    assert len(sp.get_statements("banana", quiet=True)) == 0

    sp.add("nationality", "Germany")
    claim = sp.get_statements("nationality")[0]
    assert claim.value == "de", claim
    assert claim.prop == "nationality", claim
    assert claim.prop_type == "country", claim
    assert claim.original_value == "Germany", claim

    sp.add("classification", "Banana", origin="fruit_knowledge")
    claim = sp.get_statements("classification")[0]
    assert claim.value == "Banana", claim
    assert claim.prop == "classification", claim
    assert claim.origin == "fruit_knowledge", claim

    for prop, val in sp.itervalues():
        if prop.name == "nationality":
            assert val == "de"

    pre_len = len(sp)
    sp.add("nationality", "de")
    sp.add("nationality", "it")
    sp.add("nationality", "fr")
    assert pre_len + 2 == len(sp), sp._statements["country"]
    assert len(sp.get_type_values(registry.country)) == 4

    sp.remove("nationality", "it")
    assert len(sp.get("nationality")) == 2
    sp.pop("nationality")
    assert len(sp.get("nationality")) == 0

    assert len(sp.pop("banana", quiet=True)) == 0

    stmts = list(sp.statements)
    assert len(stmts) == len(sp), stmts
    assert sorted(stmts)[0].prop == Statement.BASE


def test_advanced_props():
    dx = Dataset.make({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(dx, EXAMPLE_2)
    assert sp.last_seen is None
    now = datetime_iso(utc_now())
    assert now is not None
    for stmt in sp.statements:
        stmt.last_seen = now
    assert sp.last_seen == now

    assert len(sp.referents) == 0
    sp.extra_referents.add("banana")
    assert len(sp.referents) == 1

    assert sp.caption == "Ralph Tester"
    assert sp.pop("name") == ["Ralph Tester"]
    assert sp.caption == "info@ralphtester.me"
    sp.pop("email")
    sp.pop("phone")
    assert sp.caption == sp.schema.name
    sp.add("name", "Ralph Tester")
    assert sp.caption == "Ralph Tester"


def test_entity_merge():
    dx = Dataset.make({"name": "test", "title": "Test"})
    sp1 = StatementEntity.from_data(dx, EXAMPLE_2)
    sp2 = StatementEntity.from_data(dx, EXAMPLE_2)
    assert sp1.id == sp2.id
    assert sp1.schema.name == sp2.schema.name
    assert len(sp1) == len(sp2)

    sp1.add("alias", "Ralph")
    assert len(sp1.get_statements("alias")) == 1
    assert len(sp2.get_statements("alias")) == 0

    sp1.merge(sp2)
    assert len(sp1.get_statements("alias")) == 1


def test_other_entity():
    dx = Dataset.make({"name": "test", "title": "Test"})
    smt = Statement(
        entity_id="blubb",
        prop="name",
        schema="LegalEntity",
        value="Jane Doe",
        dataset="test",
    )
    sp = StatementEntity.from_statements(dx, [smt])
    assert sp.id == "blubb"
    assert sp.schema.name == "LegalEntity"
    assert "test" in sp.datasets
    assert sp.first_seen is None

    dt = utc_now().isoformat()
    smt2 = Statement(
        entity_id="gnaa",
        prop="birthDate",
        schema="Person",
        value="1979",
        dataset="source",
        first_seen=dt,
    )
    sp.add_statement(smt2)
    assert sp.id == "blubb"
    assert sp.schema.name == "Person"
    assert sp.first_seen == dt

    with pytest.raises(InvalidData):
        smt2 = Statement(
            entity_id="gnaa",
            prop="incorporationDate",
            schema="Company",
            value="1979",
            dataset="source",
        )
        sp.add_statement(smt2)

    with pytest.raises(InvalidData):
        sp.add("identification", "abc")
    sp.add("identification", "abc", quiet=True)

    sp.add("alias", "Harry", lang="deu")
    aliases = sp.get_statements("alias")
    assert aliases[0].lang == "deu", aliases


def test_statement_dict():
    dx = Dataset.make({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(dx, EXAMPLE_2)
    dt = utc_now().isoformat()
    sp.last_change = dt

    data = sp.to_statement_dict()
    assert data["id"] == "test"
    assert data["schema"] == "Person"
    assert data["last_change"] == dt
    assert "properties" not in data
    stmts = data["statements"]
    assert len(stmts) == len(list(sp.statements))

    sp2 = StatementEntity.from_data(dx, data)
    assert sp2.id == sp.id
    assert sp2.schema.name == sp.schema.name
    assert sp2.last_change == sp.last_change
    assert sp2.get("name") == sp.get("name")
    assert sp2.get("birthDate") == sp.get("birthDate")


def test_entity_origin():
    dx = Dataset.make({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(dx, EXAMPLE)
    data = sp.to_dict()
    assert "origin" not in data
    stmt = next(sp.statements)
    stmt.origin = "space"
    sp.add_statement(stmt)
    data = sp.to_dict()
    assert data["origin"] == ["space"]
