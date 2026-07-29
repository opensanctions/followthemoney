import pickle

from followthemoney.dataset.dataset import Dataset
from followthemoney.entity import ValueEntity
from followthemoney.proxy import EntityProxy
from followthemoney.statement.entity import StatementEntity

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
    data = {**EXAMPLE, "datasets": ["test"]}
    se = ValueEntity.from_dict(data)
    assert se.datasets == {"test"}

    # StatementEntity -> ValueEntity
    ds = Dataset({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(ds, EXAMPLE)
    se = ValueEntity.from_dict(sp.to_dict())
    assert sp.id == se.id == "jane"
    assert sp.datasets == se.datasets == {"test"}

    # ValueEntity -> StatementEntity
    data = {**EXAMPLE, "datasets": ["test"]}
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


def test_value_entity_to_dict_with_all_fields():
    """to_dict includes optional temporal fields and caption when set."""
    data = {
        **EXAMPLE,
        "datasets": ["us_ofac"],
        "referents": ["jane-alt"],
        "caption": "Jane Doe",
        "first_seen": "2024-01-01T00:00:00",
        "last_seen": "2024-06-15T00:00:00",
        "last_change": "2024-06-15T12:00:00",
    }
    ve = ValueEntity.from_dict(data)
    assert ve.first_seen == "2024-01-01T00:00:00"
    assert ve.last_seen == "2024-06-15T00:00:00"
    assert ve.last_change == "2024-06-15T12:00:00"
    assert ve._caption == "Jane Doe"

    exported = ve.to_dict()
    assert exported["caption"] == "Jane Doe"
    assert exported["first_seen"] == "2024-01-01T00:00:00"
    assert exported["last_seen"] == "2024-06-15T00:00:00"
    assert exported["last_change"] == "2024-06-15T12:00:00"
    assert "us_ofac" in exported["datasets"]
    assert "jane-alt" in exported["referents"]


def test_value_entity_merge_two_value_entities():
    """Merging two ValueEntities combines datasets, referents, and picks temporal bounds."""
    data_a = {
        **EXAMPLE,
        "datasets": ["ds_a"],
        "referents": ["ref-1"],
        "caption": "Jane Doe",
        "first_seen": "2024-03-01T00:00:00",
        "last_seen": "2024-06-01T00:00:00",
        "last_change": "2024-05-01T00:00:00",
    }
    data_b = {
        "id": "jane",
        "schema": "Person",
        "properties": {"name": ["Jane D."], "nationality": ["us"]},
        "datasets": ["ds_b"],
        "referents": ["ref-2"],
        "caption": "Jane D.",
        "first_seen": "2024-01-01T00:00:00",
        "last_seen": "2024-09-01T00:00:00",
        "last_change": "2024-08-01T00:00:00",
    }
    a = ValueEntity.from_dict(data_a)
    b = ValueEntity.from_dict(data_b)
    merged = a.merge(b)

    # datasets and referents are unioned
    assert merged.datasets == {"ds_a", "ds_b"}
    assert merged.referents == {"ref-1", "ref-2"}

    # first_seen takes the earliest, last_seen/last_change take the latest
    assert merged.first_seen == "2024-01-01T00:00:00"
    assert merged.last_seen == "2024-09-01T00:00:00"
    assert merged.last_change == "2024-08-01T00:00:00"

    # properties are merged
    assert "Jane Doe" in merged.get("name")
    assert "Jane D." in merged.get("name")
    assert "us" in merged.get("nationality")

    # caption is picked from the two candidates
    assert merged._caption in ("Jane Doe", "Jane D.")


def test_value_entity_merge_with_none_temporals():
    """Merging when one side has None temporals uses the other side's values."""
    data_a = {
        **EXAMPLE,
        "datasets": ["ds_a"],
        "first_seen": "2024-03-01T00:00:00",
    }
    data_b = {
        "id": "jane",
        "schema": "Person",
        "properties": {"name": ["Jane D."]},
        "datasets": ["ds_b"],
    }
    a = ValueEntity.from_dict(data_a)
    b = ValueEntity.from_dict(data_b)
    merged = a.merge(b)

    assert merged.first_seen == "2024-03-01T00:00:00"
    assert merged.last_seen is None
    assert merged.last_change is None


def test_value_entity_merge_with_entity_proxy():
    """Merging a ValueEntity with a plain EntityProxy skips VE-specific fields."""
    ve = ValueEntity.from_dict({
        **EXAMPLE,
        "datasets": ["ds_a"],
        "first_seen": "2024-01-01T00:00:00",
    })
    proxy = EntityProxy.from_dict({
        "id": "jane",
        "schema": "Person",
        "properties": {"nationality": ["gb"]},
    })
    merged = ve.merge(proxy)

    # base properties are merged
    assert "gb" in merged.get("nationality")
    # VE fields are unchanged (not wiped)
    assert merged.datasets == {"ds_a"}
    assert merged.first_seen == "2024-01-01T00:00:00"


def test_value_entity_checksum_components():
    """Checksum incorporates datasets, referents, and last_change."""
    base = {**EXAMPLE, "datasets": ["ds_a"]}
    ve_a = ValueEntity.from_dict(base)
    ve_b = ValueEntity.from_dict({**EXAMPLE, "datasets": ["ds_b"]})
    ve_none = ValueEntity.from_dict(EXAMPLE)
    ve_ref = ValueEntity.from_dict({**base, "referents": ["jane-alt"]})
    ve_change = ValueEntity.from_dict({**base, "last_change": "2024-06-01T00:00:00"})

    checksums = {ve_a.checksum, ve_b.checksum, ve_none.checksum,
                 ve_ref.checksum, ve_change.checksum}
    assert len(checksums) == 5


def test_value_entity_statements_schema_upgrade():
    """When statements carry a more specific schema, the entity schema is upgraded."""
    ds = Dataset({"name": "test", "title": "Test"})
    sp = StatementEntity.from_data(ds, {
        "id": "acme",
        "schema": "LegalEntity",
        "properties": {"name": ["ACME Corp"]},
    })
    stmt_data = sp.to_statement_dict()

    # Patch statements to carry a more specific schema
    for stmt in stmt_data["statements"]:
        stmt["schema"] = "Company"

    ve = ValueEntity.from_dict(stmt_data)
    assert ve.schema.name == "Company"


def test_value_entity_clone_preserves_fields():
    """Cloning a ValueEntity preserves all VE-specific fields and is independent."""
    data = {
        **EXAMPLE,
        "datasets": ["ds_a"],
        "referents": ["ref-1"],
        "caption": "Jane Doe",
        "first_seen": "2024-01-01T00:00:00",
        "last_seen": "2024-06-15T00:00:00",
        "last_change": "2024-06-15T12:00:00",
    }
    original = ValueEntity.from_dict(data)
    cloned = original.clone()

    assert cloned.datasets == original.datasets
    assert cloned.referents == original.referents
    assert cloned._caption == original._caption
    assert cloned.first_seen == original.first_seen
    assert cloned.last_seen == original.last_seen
    assert cloned.last_change == original.last_change
    assert cloned.checksum == original.checksum

    # clone is independent
    cloned.datasets.add("ds_b")
    assert "ds_b" not in original.datasets


def test_value_entity_pickle():
    original = ValueEntity.from_dict({"id": "1", "schema": "Person"})
    pickled = pickle.dumps(original)
    unpickled = pickle.loads(pickled)
    assert unpickled == original
    assert unpickled.schema is original.schema
