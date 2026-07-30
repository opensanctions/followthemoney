from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from followthemoney.dataset import UndefinedDataset
from followthemoney.statement import Statement, read_path_statements, write_statements
from followthemoney.statement.entity import StatementEntity
from followthemoney.statement.serialize import CSV, JSON, PACK, read_statements

EXAMPLE = {
    "id": "bla",
    "schema": "Person",
    "properties": {"name": ["John Doe"], "birthDate": ["1976"]},
}


def test_json_statements():
    with TemporaryDirectory() as tmpdir:
        entity = StatementEntity.from_data(UndefinedDataset, EXAMPLE)
        path = Path(tmpdir) / "statement.json"
        with open(path, "wb") as fh:
            write_statements(fh, JSON, entity.statements)
        stmts = list(read_path_statements(path, JSON))
        assert len(stmts) == 3
        for stmt in stmts:
            assert stmt.canonical_id == "bla", stmt
            assert stmt.entity_id == "bla", stmt
            assert stmt.schema == "Person", stmt


def test_csv_statements():
    with TemporaryDirectory() as tmpdir:
        entity = StatementEntity.from_data(UndefinedDataset, EXAMPLE)
        path = Path(tmpdir) / "statement.csv"
        with open(path, "wb") as fh:
            write_statements(fh, CSV, entity.statements)
        stmts = list(read_path_statements(path, CSV))
        assert len(stmts) == 3, stmts
        for stmt in stmts:
            assert stmt.canonical_id == "bla", stmt
            assert stmt.entity_id == "bla", stmt
            assert stmt.schema == "Person", stmt


def test_pack_statements():
    with TemporaryDirectory() as tmpdir:
        entity = StatementEntity.from_data(UndefinedDataset, EXAMPLE)
        path = Path(tmpdir) / "statement.pack"
        with open(path, "wb") as fh:
            write_statements(fh, PACK, entity.statements)
        stmts = list(read_path_statements(path, PACK))
        assert len(stmts) == 3, stmts
        for stmt in stmts:
            assert stmt.canonical_id == "bla", stmt
            assert stmt.entity_id == "bla", stmt
            assert stmt.schema == "Person", stmt


def test_pack_statements_legacy_no_header():
    # Legacy pack files have no header row; the first row is data and
    # must not be dropped.
    legacy = (
        '"e1","Person:name","Alice","ds","","","","f","2020","2020"\n'
        '"e2","Person:name","Bob","ds","","","","f","2020","2020"\n'
    )
    stmts = list(read_statements(BytesIO(legacy.encode("utf-8")), PACK))
    assert len(stmts) == 2, stmts
    assert [s.entity_id for s in stmts] == ["e1", "e2"]


def test_csv_statements_none_round_trip():
    stmt = Statement(
        entity_id="e1",
        prop="name",
        schema="Person",
        value="John Doe",
        dataset="ds",
    )
    assert stmt.first_seen is None
    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "statement.csv"
        with open(path, "wb") as fh:
            write_statements(fh, CSV, [stmt])
        read = next(iter(read_path_statements(path, CSV)))
    assert read.first_seen is None
    assert read.last_seen is None
    assert read.id == stmt.id


def test_csv_statements_crlf_value():
    for format in (CSV, PACK):
        stmt = Statement(
            entity_id="e1",
            prop="notes",
            schema="Person",
            value="line1\r\nline2",
            dataset="ds",
        )
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "statement.dat"
            with open(path, "wb") as fh:
                write_statements(fh, format, [stmt])
            read = next(iter(read_path_statements(path, format)))
        assert read.value == "line1\r\nline2", format
        assert read.id == stmt.id == read.generate_key(), format
