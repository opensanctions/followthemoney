import io
import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from followthemoney import model
from followthemoney.cli.util import write_entity

FIXTURES_PATH = Path(__file__).parent.joinpath("fixtures/")


@pytest.fixture(scope="module")
def catalog_path():
    return FIXTURES_PATH.joinpath("catalog.yml")


@pytest.fixture(scope="module")
def kekmeta_path():
    return FIXTURES_PATH.joinpath("kekmeta.yml")


@pytest.fixture(scope="module")
def catalog_data(catalog_path):
    with open(catalog_path, "r") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="module")
def cli_runner():
    return CliRunner()


@pytest.fixture(scope="module")
def entity_jsonl():
    """8712 Company/Ownership entities as JSONL bytes from KEK fixture."""
    db_path = FIXTURES_PATH.joinpath("kek.sqlite")
    os.environ["FTM_TEST_DATABASE_URI"] = "sqlite:///" + str(db_path)
    mapping_path = FIXTURES_PATH.joinpath("kek.yml")
    with open(mapping_path, "r") as fh:
        kek_mapping = yaml.safe_load(fh)
    buf = io.BytesIO()
    for entity in model.map_entities(kek_mapping):
        write_entity(buf, entity)
    return buf.getvalue()
