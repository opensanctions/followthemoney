# Datasets and data catalogs

FollowTheMoney entities are often grouped into datasets, which might can the source or purpose of the set. Providing metadata on the sources can add to the usability of FtM data products, so we've set up a simple specification for metadata exchange.

Since normal FtM entity streams do not contain dataset metadata, a [ValueEntity][followthemoney.entity.ValueEntity] exists, which puts in place a link between dataset metadata and individual entities. Users of the [statement data model](statements.md) need to specify a dataset for each statement they generate.

## Data catalogs

Metadata is published in two different forms: as a dataset index file, or as a data catalog. Catalogs combine the metadata for multiple datasets into one file, with metadata for each dataset included in an array named `datasets`.

## Dataset metadata {: #dataset}

The most important piece of metadata for any dataset is its `name`. Names are lowercase, underscore-linked short identifiers (eg. `us_ofac_sdn`) used in the actual entity data to reference a data source. Inside the metadata (or a catalog entry), the following fields can be found:

| **Section**          | **Field**         | **Description**    |
|----------------|---------------|---------------------------|
| `dataset`        |               |  |
|                | `name`          | Dataset’s unique identifier |
|                | `title`         | Human-readable title |
|                | `summary`       | Short summary string |
|                | `description`   | Detailed description of the dataset in markdown syntax |
|                | `tags`          | List of tags assigned to this dataset |
|                | `index_url`     | URL to dataset metadata file |
|                | `version`       | Latest dataset version. Each data update produces a new version ID, and version IDs can be relied on to be sortable strings.  |
|                | `last_change`   | Timestamp when any entity in the dataset last changed. This marks when the system discovered the change, not when published at source. Also note that changes to our data cleaning tools may result in changes reflected here as well. |
|                | `last_export`   | Timestamp of the most recent dataset crawl and export. This is the time of when the process in question was started, not when the resulting data was uploaded to our public archive.  |
|        | `datasets`              | All data sources (and enrichment datasets) included in this collection |
|                | `resources`     | Array of objects describing associated files, including exports and source data.  |
|         | `updated_at`    | Use `last_export` instead. |
| `coverage`       |               | Coverage metadata object. |
|                | `start`         | Date of the first time the dataset was included in the database. |
|                | `countries`     | List of the countries covered by this dataset. |
|                | `frequency`     | One of: `never`, `hourly`, `daily`, `weekly`, `monthly`, `annually` |
|                | `schedule`      | A more precise (cron-style) specification of the update frequency |
| `publisher`      |               |  |
|                | `name`          | Publishing source name  |
|                | `acronym`       | Pubshlishing source acronym (e.g. OFAC) |
|                | `description`   | Detailed description of publishing source, uses markdown. |
|                | `url`           | Link to the publisher's home page |
|                | `country`       | Originating country (code) of publishing source |
|                | `country_label` | Originating country (name) of publishing source |
|                | `official`      | `true` if the publisher is a government or inter-governmental organization. |
| `resources` |                   |                                                        |
|             | `name`            | Identifier for this export                             |
|             | `url`             | Direct download URL where the resource file is fetched |
|             | `checksum`        | SHA1 of the resource contents                          |
|             | `mime_type`       | The MIME type of the resource (eg. text/csv)           |
|             | `mime_type_label` | Human-readable label for the MIME type                 |
|             | `title`           | Title of the resource                                  |
|             | `size`            | Size of the resource in bytes                          |


## Dataset query DSL

The Python library includes a small query DSL for filtering datasets by name, collection membership, or tags. It is available as `followthemoney.dataset.evaluate_query`:

```python
from followthemoney.dataset import DataCatalog, Dataset, evaluate_query

catalog = DataCatalog.from_path(Dataset, "catalog.yml")
results = evaluate_query(catalog, {"and": ["#issuer.eu", "#list.sanction"]})
```

### Grammar

A query is a recursive structure with three operators and string leaves:

```
DatasetQuery = str | list[DatasetQuery]
             | {"or": list[DatasetQuery]}
             | {"and": list[DatasetQuery]}
             | {"not": DatasetQuery}
```

### Leaf values

| Pattern | Meaning | Example |
|---------|---------|---------|
| `"datasetname"` | A specific dataset by slug | `"us_ofac_sdn"` |
| `"collectionname"` | A collection, expanded to its leaf datasets | `"sanctions"` |
| `"#tag"` | All datasets matching a tag | `"#issuer.eu"` |

The `#` prefix is query syntax only — the stored tag value is `issuer.eu`, not `#issuer.eu`. Collections are always expanded to their leaf datasets.

### Operators

**`or`** — union of all sub-queries:

```json
{"or": ["#list.sanction", "#list.debarment"]}
```

**`and`** — intersection of all sub-queries:

```json
{"and": ["#issuer.eu", "#list.sanction"]}
```

**`not`** — complement (all datasets in the catalog *except* the matched ones):

```json
{"not": "lt_fiu_sanctions"}
```

A bare list is shorthand for `or`, so `["a", "b"]` is equivalent to `{"or": ["a", "b"]}`.

### Examples

A single dataset:

```json
"us_ofac_sdn"
```

Multiple datasets:

```json
["us_ofac_sdn", "eu_fsf", "gb_hmt_sanctions"]
```

All datasets tagged as sanctions:

```json
"#list.sanction"
```

EU-issued sanctions lists:

```json
{"and": ["#issuer.eu", "#list.sanction"]}
```

Western sanctions and debarments, excluding a specific dataset and all Russian-issued sources:

```json
{"and": [
    {"or": ["#issuer.west", "#list.sanction", "#list.debarment"]},
    {"not": "lt_fiu_sanctions"},
    {"not": "#issuer.ru"}
]}
```

Exclude multiple datasets at once using nested `not`/`or`:

```json
{"and": [
    "#list.sanction",
    {"not": {"or": ["lt_fiu_sanctions", "ru_fedsfm"]}}
]}
```

### String syntax

For use in URLs, CLI arguments, or configuration files, queries can also be written as compact strings using `parse_query`:

```python
from followthemoney.dataset import parse_query, evaluate_query

query = parse_query("(#issuer.west|#list.sanction)-lt_fiu-#issuer.ru")
results = evaluate_query(catalog, query)
```

The string syntax uses three operators, listed by precedence (high to low):

| Operator | Meaning | JSON equivalent |
|----------|---------|-----------------|
| `()` | Grouping | Nesting |
| `&` | Intersection | `and` |
| `-` | Subtraction | `and` + `not` |
| `\|` | Union | `or` |

`&` and `-` bind tighter than `|`, so `a|b&c` is parsed as `a|(b&c)`.

Subtraction desugars into `and` + `not`:

| String | JSON AST |
|--------|----------|
| `sanctions` | `"sanctions"` |
| `a\|b\|c` | `{"or": ["a", "b", "c"]}` |
| `a&b` | `{"and": ["a", "b"]}` |
| `a-b` | `{"and": ["a", {"not": "b"}]}` |
| `(a\|b)-c` | `{"and": [{"or": ["a", "b"]}, {"not": "c"}]}` |
| `(#issuer.west\|#list.sanction)-lt_fiu-#issuer.ru` | `{"and": [{"or": ["#issuer.west", "#list.sanction"]}, {"not": "lt_fiu"}, {"not": "#issuer.ru"}]}` |

## Relevant standards

The dataset specification in FtM is largely based on Google's [schema.org/Dataset](https://schema.org/Dataset), which allows for SEO-friendly markup on dataset pages. Various similar specifications exist, for example the W3C's [Data Catalog Vocabulary (DCAT)](https://www.w3.org/TR/vocab-dcat-3/) and the [Frictionless Data Package](https://specs.frictionlessdata.io/data-package/).

All of these specifications are roughly compatible, and it should be easy to import or export FtM metadata into any of them. 