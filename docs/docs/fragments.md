---
title: 'Entity Fragmentation'
---

# Entity Fragmentation

Generating graph data is a difficult process. The size of the datasets we want to process using FtM makes it difficult to incrementally build nodes and edges in memory like you would in many data science workflows. Instead, we use a stream-based solution for constructing graph entities. That is why the toolkit supports _entity fragments_ and [_aggregation_](#aggregation).

## Example

To illustrate the problem, imagine a table with millions of rows that describes a set of people and the companies they control. Every company can have multiple directors, while each director might control multiple companies:

| CompanyID | CompanyName            | DirectorName | DirectorIdNo | DirectorDoB |
| --------- | ---------------------- | ------------ | ------------ | ----------- |
| A123      | Brilliant Amazing Ltd. | John Smith   | PP827817     | 1979-02-16  |
| A71882    | Goldfish Ltd.          | John Smith   | PP827817     | NULL        |
| A123      | Brilliant Amazing Ltd. | Jane Doe     | PP1988299    | 1983-06-24  |

When [turning this data into FtM](mappings.md), we’d create three entities for each row: a {{ schema_ref('Company') }}, a {{ schema_ref('Person') }} and a {{ schema_ref('Directorship') }} that connects the two.

If we do this row by row, we’d eventually generate three {{ schema_ref('Company') }} entities to represent two actual companies, and three {{ schema_ref('Person') }} entities that describe two distinct people. The generated entities are _fragmented_, ie. multiple references to the same entity ID are generated at different times in the program.

Another example: a document processing pipeline may first receive a {{ schema_ref('Document') }} and store its checksum and file name, then submit it for a processing to a queue. There, a content extractor may output a body text, and then a separate process performing NLP analysis contributes annotations like the names of individuals and companies mentioned in the document. Again, each step in processing has emitted _fragments_ of the eventual entity.

Of course, we could treat each change to an entity as an update to a normal database backend, like an ElasticSearch index: fetch the existing entity, merge the changes, update the index. This, again, runs into scalability issues and race conditions in parallelized processing environments.

A better solution is to store the generated entity fragments as they are produced and to [aggregate](#aggregation) (combine) them into full entities when needed - often during a search indexing or data export process. 

## Entity aggregation {: #aggregation}

Entity aggregation requires sorting all generated fragments so they can be iterated in sequence of the entity ID that they are a part of. There are several techniques for doing so:

* **In-memory:** for small datasets, it can be easiest to load all fragments into memory in order to merge them. The [command-line](cli.md) tool `ftm aggregate` will do this.
* **In a database:** the entity fragments are written to a SQL database, and then iterated as the result of a sorting query. The [followthemoney-store](https://github.com/alephdata/followthemoney-store) library allows you to do this in a SQLite or PostgreSQL database.
* **Using flat files:** FtM's JSON exporter will emit data that can be sorted using the generic `sort` command-line tool. The `ftm sorted-aggregate` command will then aggregate the resulting stream of sorted entity data.
* **Using statements:** the [statement data model](statements.md) provides an alternative to the idea of _fragmentation_. Instead of splitting entities into partial entity fragments, they are divided into statements, which are even more granular. Statements [can also be aggregated](statements.md#aggregation).

### Using followthemoney-store

```bash
# Generate entities from a CSV file and a mapping:
cat company-registry.csv | ftm map-csv mapping_file.yml > fragments.ijson

# Write the fragments to a table `company_registry`:
cat fragments.ijson | ftm store write -d company_registry

# List the tables in the store:
ftm store list

# Output merged entities:
ftm store iterate -d company_registry
```

The same functionality can also be used as a Python library:

```python
import os
from ftmstore import get_dataset
# Assume a function that will emit fragments:
from myapp.data import generate_fragments

# If no `database_uri` is given, ftmstore will read connection from
# $FTM_STORE_URI, or create a file called `followthemoney.sqlite` in
# the current directory.
database_uri = os.environ.get('DATABASE_URI')
dataset = get_dataset('myapp_dataset', database_uri=database_uri)
bulk = dataset.bulk()
for idx, proxy in enumerate(generate_fragments()):
    bulk.put(proxy, fragment=idx)
bulk.flush()

# This will print the number of combined entities (ie. DISTINCT id):
print(len(dataset))

# This will return combined entities:
for entity in dataset.iterate():
    print(entity.caption)

# You could also iterate the underlying fragments:
for proxy in dataset.partials():
    print(proxy)

# Note: `dataset.partials()` returns `EntityProxy` objects. The method
# `dataset.fragments()` would return raw Python dictionaries instead.

# All three methods also support the `entity_id` filter, which can also be
# shortened to `get`:
entity = dataset.get(entity_id)
```

### Fragment origins

`followthemoney-store` is used across the tools built on FtM to capture and aggregate entity fragments. In Aleph, fragments for one entity might be written by different processes: the API, document ingestors, document NER analyzers or a translation backend. It is convenient to be able to flush all entity fragments from a particular origin, while leaving the other fragments intact. For example, this can be used to delete all data uploaded via the bulk API, while leaving document-based data in the same dataset intact.

To support this, ftm-store has the notion of an origin for each fragment. If specified, this can be used to later delete or overwrite subsets of fragments.

```bash
cat us_ofac.ijson | ftm store write -d sanctions -o us_ofac
cat eu_eeas.ijson | ftm store write -d sanctions -o eu_eeas

# Will now have entities from both source files:
ftm store iterate -d sanctions | wc -l

# Delete all fragments from the second file:
ftm store delete -d sanctions -o eu_eeas

# Only one source file is left:
ftm store iterate -d sanctions | wc -l
```
