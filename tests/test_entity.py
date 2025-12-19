import pickle
from followthemoney.dataset.dataset import Dataset
from followthemoney.statement.entity import StatementEntity
from followthemoney.entity import ValueEntity


EXAMPLE = {
    "id": "jane",
    "schema": "Person",
    "properties": {"name": ["Jane Doe"], "birthDate": ["1976"]},
}


def test_value_entity():
    se = ValueEntity.from_dict(EXAMPLE)
    assert se.schema.name == "Person"
    assert se.id == "jane"
    assert se.caption == "Jane Doe"
    assert se.checksum == "b0139596060f3193e4994484870070638f287e6c"
    assert se.datasets == set()
    exported = se.to_dict()
    assert exported == {
        "id": "jane",
        # "caption": "Jane Doe",
        "schema": "Person",
        "properties": {"name": ["Jane Doe"], "birthDate": ["1976"]},
        "referents": [],
        "datasets": [],
    }

    # with dataset
    data = {**EXAMPLE, **{"datasets": ["test"]}}
    se = ValueEntity.from_dict(data)
    assert se.datasets == {"test"}

    # StatementEntity -> ValueEntity
    ds = Dataset({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(ds, EXAMPLE)
    se = ValueEntity.from_dict(sp.to_dict())
    assert sp.id == se.id == "jane"
    assert sp.datasets == se.datasets == {"test"}

    # ValueEntity -> StatementEntity
    data = {**EXAMPLE, **{"datasets": ["test"]}}
    se = ValueEntity.from_dict(data)
    sp = StatementEntity.from_data(ds, se.to_dict())
    assert sp.id == se.id == "jane"
    assert hash(se) == hash(sp)
    assert sp.datasets == se.datasets == {"test"}
    assert se.checksum != sp.checksum

    # with statements list in payload
    data = sp.to_statement_dict()
    s1 = data["statements"][0]
    # patch other entity id & dataset
    s1["entity_id"] = "jane1"
    s1["dataset"] = "other"
    data["statements"][0] = s1

    se = ValueEntity.from_dict(data)
    assert se.referents == {"jane1"}
    assert se.datasets == {"other", "test"}
    assert se.caption == "Jane Doe"


def test_statement_entity():
    ds = Dataset({"name": "test", "title": "Test"})
    se = StatementEntity.from_data(ds, EXAMPLE)
    assert se.id == "jane"
    exported = se.to_statement_dict()
    assert "statements" in exported
    se = ValueEntity.from_dict(exported)
    assert se.get("name") == ["Jane Doe"]


def test_value_entity_pickle():
    original = ValueEntity.from_dict({"id": "1", "schema": "Person"})
    pickled = pickle.dumps(original)
    unpickled = pickle.loads(pickled)
    assert unpickled == original
    assert unpickled.schema is original.schema
