import json
from pydantic import ValidationError
import pytest
from pathlib import Path
from typing import Any, Dict
from tempfile import TemporaryDirectory

from followthemoney.dataset import DataCatalog, Dataset
from followthemoney.dataset.dataset import DatasetModel


def test_donations_base(catalog_data: Dict[str, Any]):
    catalog = DataCatalog(Dataset, catalog_data)
    assert len(catalog.datasets) == 5, catalog.datasets
    ds = catalog.get("donations")
    assert ds is not None, ds
    assert ds.name == "donations"
    assert not ds == "donations"
    assert ds.model.publisher is None
    assert ds.to_dict().get("publisher") is None
    assert len(ds.model.resources) == 2, ds.model.resources
    for res in ds.model.resources:
        assert res.name is not None
        if res.mime_type is None:
            assert res.mime_type_label is None

    assert ds.get_resource("donations.csv") is not None
    with pytest.raises(ValueError):
        ds.get_resource("donations.dbf")

def test_donations_export(catalog_data: Dict[str, Any]):
    export = DataCatalog(Dataset, catalog_data).get("donations").to_dict()
    assert "publisher" not in export

    assert export["resources"][0]["name"] == "donations.csv"
    assert export["resources"][0]["mime_type"] == "text/csv"
    assert export["resources"][0]["mime_type_label"] == "Comma-separated table"

    assert export["resources"][1]["name"] == "donations.ijson"
    assert export["resources"][1].get("mime_type") is None
    assert export["resources"][1].get("mime_type_label") is None


def test_company_dataset(catalog_data: Dict[str, Any]):
    catalog = DataCatalog(Dataset, catalog_data)
    assert len(catalog.datasets) == 5, catalog.datasets
    ds = catalog.get("company_data")
    assert ds is not None, ds
    assert ds.name == "company_data"
    assert ds.model.publisher is not None
    assert ds.model.publisher.country == "us"
    assert ds.model.publisher.country_label == "United States of America"
    assert ds.model.coverage is not None
    assert "coverage" in ds.to_dict()
    assert ds.model.coverage.start == "2005"
    assert ds.model.coverage.end == "2010-01"
    assert "us" in ds.model.coverage.countries

    assert "company_data" in repr(ds)

    other = Dataset.make({"name": "company_data", "title": "Company data"})
    assert other == ds, other


def test_create():
    catalog = DataCatalog(Dataset, {})
    assert len(catalog.datasets) == 0, catalog.datasets

    with pytest.raises(ValidationError):
        catalog.make_dataset({})

    ds = catalog.make_dataset({"name": "test_dataset"})
    assert ds.name == "test_dataset"
    ds = ds.model
    assert ds.title == "test_dataset"
    assert ds.license is None
    assert ds.summary is None


def test_hierarchy(catalog_data: Dict[str, Any]):
    catalog = DataCatalog(Dataset, catalog_data)
    all_datasets = catalog.require("all_datasets")
    collection_a = catalog.require("collection_a")
    leak = catalog.require("leak")
    assert leak not in collection_a.datasets
    assert collection_a not in collection_a.children
    assert leak in all_datasets.datasets
    assert len(all_datasets.children) == 2, all_datasets.children
    assert len(all_datasets.datasets) == 5, all_datasets.datasets
    assert len(all_datasets.dataset_names) == len(all_datasets.datasets)
    assert len(all_datasets.leaves) == len(all_datasets.leaf_names)


def test_from_path(catalog_path: Path):
    catalog = DataCatalog.from_path(Dataset, catalog_path)
    assert len(catalog.datasets) == 5, catalog.datasets

    data = catalog.to_dict()
    assert isinstance(data, dict)
    assert "datasets" in data

    ds = catalog.get("donations")
    assert ds is not None, ds
    assert ds.name == "donations"

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "dataset.json"
        with open(path, "w") as fh:
            json.dump(ds.to_dict(), fh, indent=2)

        ds_load = Dataset.from_path(path)
        ds_load = ds_load.model
        assert ds_load.name == ds.name
        assert ds_load.title == "Political party donations"


def test_dataset_aleph_metadata(catalog_data: Dict[str, Any]):
    catalog = DataCatalog(Dataset, catalog_data)
    ds = catalog.require("leak")
    ds = ds.model
    assert ds.category == "leak"
    assert ds.coverage is not None
    assert ds.coverage.frequency == "never"

    # invalid metadata
    with pytest.raises(ValidationError):
        meta = {
            "name": "invalid",
            "title": "Invalid metadata",
            "coverage": {"frequency": "foo"},
        }
        ds = Dataset(meta)


def test_dataset_name_validation():
    with pytest.raises(ValueError):
        Dataset({"name": "my dataset"})
    with pytest.raises(ValueError):
        Dataset({"name": "my-dataset"})
    with pytest.raises(ValueError):
        Dataset({"name": "My_dataset"})
    with pytest.raises(ValueError):
        Dataset({"name": "_test"})
    with pytest.raises(ValueError):
        Dataset({"name": "ä_dataset"})
    with pytest.raises(ValueError):
        Dataset({"name": "another.invalid.name"})


def test_catalog_model(catalog_data: Dict[str, Any]):
    catalog = DataCatalog(Dataset, catalog_data)
    assert len(catalog.datasets) == 5
    ds = catalog.datasets[0]
    assert isinstance(ds.model, DatasetModel)

    mdl = catalog.require("donations").model
    assert mdl.title == "Political party donations"
    res = mdl.resources[0]
    assert res.name == "donations.csv"
