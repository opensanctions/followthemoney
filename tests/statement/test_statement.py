import pytest
from followthemoney.dataset.dataset import Dataset
from followthemoney.statement.entity import StatementEntity
from followthemoney.statement.statement import Statement


def test_statement_state():
    stmt = Statement(
        schema="Person",
        entity_id="entity1",
        prop="name",
        value="Alice",
        dataset="test-dataset",
        lang="eng",
        original_value="Alice",
        first_seen="2024-01-01T00:00:00Z",
        external=False,
        canonical_id="canonical-123",
        last_seen="2024-01-02T00:00:00Z",
        origin="imported",
    )
    assert stmt.lang == "eng"
    assert stmt.canonical_id == "canonical-123"
    assert stmt.id is not None

    ostmt = stmt.clone(lang="fra")
    assert ostmt.lang == "fra"
    assert ostmt.canonical_id == "canonical-123"
    assert ostmt.id != stmt.id

    xstmt = stmt.clone(canonical_id="canonical-456")
    assert xstmt.lang == "eng"
    assert xstmt.canonical_id == "canonical-456"
    assert xstmt.id == stmt.id

    with pytest.raises(AttributeError):
        stmt.lang = "spa"  # type: ignore


def test_statement_external():
    data = {
        "id": "entity2",
        "schema": "Person",
        "properties": {"name": ["Bob"]},
    }
    dx = Dataset.make({"name": "test", "title": "Test"})
    entity = StatementEntity.from_data(dx, data, external=True)
    stmts = list(entity.statements)
    assert len(stmts) == 2
    for stmt in stmts:
        assert stmt.external is True
