# Statement-based data model

The primary unit of the FollowTheMoney (FTM) data model is an entity, defined by a schema like Person, Company, or Ownership, an ID, and a set of properties like their name, birth date or jurisdiction. Sometimes, however, there’s a need to store additional information about each value assigned to a property: the name property value “John Doe”, for example, may be sourced from a specific dataset, first seen by a crawler at a particular time, or we might know the language it’s written in. 

`Statements` capture details about such property value metadata. Often, a statement is a row in a JSON/CSV file or SQL database, identifying the ID of the entity it belongs to, the property it describes, a value, and various other metadata. Multiple statements can be assembled into an FtM entity (a [StatementEntity][followthemoney.statement.entity.StatementEntity]), and any FtM entity can be unrolled into a corresponding set of statements. 

Statements have multiple benefits in processing FtM data:

- They can be used to **store property metadata**, allowing for fine-grained provenance of data, language and temporal metadata, or storing the property value prior to data normalization (e.g. an unformatted date, or a country name that was converted to a country code).
- Statements also offer an **alternative method for entity aggregation**: fragmented entities can be turned into statements, and then the statements can be sorted by their entity ID and eventually assembled into aggregated entities. This is particularly fun because JSON-based statement data can be sorted using common command line tools (like `sort` or `terashuf`), rather than requiring a database.
- Statement-based entity aggregation can be used to perform **entity integration and deduplication**. If we know that entities with the IDs `a` and `b` are the same logical person or company, adding a combined “canonical ID” before aggregation will collapse the two entities into one combined profile. Meanwhile, the metadata included in each statement still lets us identify the origin of each property value.

## Data format

As a database schema, this results in a table with the following columns:

| Column | Type | Length | Description |
| ------ | ---- | ------ | ----------- |
| ``entity_id`` | ID | 255 | (source ID): the entity identifier as derived from the data source. This is often a unique hash derived from several properties of an entity. |
| ``prop`` | string | 255 | (property): the entity attribute that this statement relates to, eg. {{ prop_ref('Person:birthDate') }}, or {{ prop_ref('Thing:name') }}. |
| ``prop_type`` | string | 255 | (property type): the data type of the given property, eg. ``date``, ``country``, ``name`` etc. |
| ``value`` | string | 65535 | Actual value of the property for the entity. If multiple values are indicated in the source data, each of them will result in a separate statement. |
| ``lang`` | string | 3 | Language (3 letter code) of the value, if it is known. |
| ``original_value`` | string | 65535 | Property value before it was cleaned (e.g. country name vs. code, unparsed date). |
| ``dataset`` | string | 255 | [Source dataset](metadata.md#dataset) identifier (same as the dataset name). |
| ``origin`` | string | 255 | A descriptor of the mechanism which generated this statement, eg. a processing phase or source file name. |
| ``schema`` | string | 255 | Type of the given entity. Statements related to one entity can indicate more or less specific schemata, e.g. {{ schema_ref('LegalEntity') }} and {{ schema_ref('Company') }} (the resulting entity would be a {{ schema_ref('Company') }}). If the statements reflect schemata that cannot be merged, an exception will be raised. |
| ``first_seen`` | iso_ts | | First date when the processing pipeline found this value linked to the given entity. Please note that this only records values after July 2021, when we started tracking the data - more realistic evidence of when an entity was added to the given data source can be found in the ``createdAt`` property. |
| ``last_seen`` | iso_ts | | Latest date when the processing pipeline found this value.
| ``external`` | boolean | | External statements are suggested additions to a dataset, pending human-in-the-loop approval. Used in `nomenklatura`. |
| ``canonical_id`` | ID | 255 | Deduplicated entity ID. This is the ID of a clustered entity profile in which the entity `entity_id` has been subsumed. |

## Command-line usage

The [command-line tool](cli.md) `ftm` provides some basic functions for working with statement data:

```bash
# Convert "traditional" FtM entities to a statement stream
cat entities.ftm.json | ftm statements --format json -o statements.json
#. The inverse operation:
ftm aggregate-statements -i statements.json -o entities.ftm.json
```

While the default serialization for statement data is a line-based JSON format, the data can also be converted to a CSV file like this:

```bash
cat entities.ftm.json | ftm statements --format csv -o statements.csv
# Or, for an existing statement data file:
ftm format-statements -f json -i statements.json -x csv -o statements.csv
```

### File-based entity aggregation {: #aggregation}

When represented as statements, FtM entity data can be sorted to perform aggregation. Consider this example:

```bash
# Map several source files to FtM. Some of the source files may emit copies of
# the same entity.
ftm map-csv mapping.yml -i source1.csv | ftm statements -o source1.json
ftm map-csv mapping.yml -i source2.csv | ftm statements -o source2.json
ftm map-csv mapping.yml -i source3.csv | ftm statements -o source3.json

# Invoke a normal UNIX sort:
sort -o combined.json source1.json source2.json source3.json 

# Now, all statements representing one entity are grouped and can be turned
# into FtM entities:
ftm aggregate-statements -i combined.json -o entities.ftm.json
```

Of course, the same process can be conducted with statements located in another storage system, e.g. a key-value store or database.

Importantly, the statements will be sorted by `canonical_id`, which can be a cluster ID derived from their original `entity_id`.

The `nomenklatura` toolkit, which is built on top of FtM, uses this to perform de-duplication of data from multiple sources prior to their eventual assembly into complex FtM JSON entities.