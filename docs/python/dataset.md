# Datasets and catalogs

Python API for loading, constructing, and filtering FtM datasets and data catalogs. For the conceptual model and the YAML structure, see [Datasets and data catalogs](../docs/metadata.md).

A typical usage pattern is to load a catalog from a YAML file, look up a dataset by name, and iterate its resources:

```python
from followthemoney.dataset import DataCatalog, Dataset

catalog = DataCatalog.from_path(Dataset, "catalog.yml")
ofac = catalog.require("us_ofac_sdn")
for resource in ofac.resources:
    print(resource.name, resource.url)
```

For filtering a catalog against a [dataset query](../docs/metadata.md#dataset-query-dsl), use `evaluate_query` or `match_datasets`:

```python
from followthemoney.dataset import evaluate_query, parse_query

query = parse_query("#list.sanction & #issuer.eu")
matched = evaluate_query(catalog, query)
```

## Catalog

::: followthemoney.dataset.DataCatalog
    options:
        heading_level: 3
        show_source: false

## Dataset

::: followthemoney.dataset.Dataset
    options:
        heading_level: 3
        show_source: false

## Dataset metadata sub-objects

::: followthemoney.dataset.DataResource
    options:
        heading_level: 3
        show_source: false

::: followthemoney.dataset.DataPublisher
    options:
        heading_level: 3
        show_source: false

::: followthemoney.dataset.DataCoverage
    options:
        heading_level: 3
        show_source: false

## Query functions

::: followthemoney.dataset.evaluate_query
    options:
        heading_level: 3
        show_source: false

::: followthemoney.dataset.match_datasets
    options:
        heading_level: 3
        show_source: false

::: followthemoney.dataset.parse_query
    options:
        heading_level: 3
        show_source: false

::: followthemoney.dataset.validate_query
    options:
        heading_level: 3
        show_source: false
