---
title: Introduction
---

# Introduction

FollowTheMoney (FtM) defines a simple data model for storing complex object graphs. You will need to understand three concepts: entities, entity references, and entity streams.

## Entities

Entities are often expressed as snippets of JSON, with three standard fields: a unique `id`, a specification of the type of the entity called `schema`, and a set of `properties`. `properties` are multi-valued and values are always strings.

```json
{
  "id": "1b38214f88d139897bbd13eabde464043d84bbf9",
  "schema": "Person",
  "properties": {
    "name": ["John Doe"],
    "nationality": ["us", "au"],
    "birthDate": ["1982"]
  }
}
```

Property names are defined by the [_schemata_](../explorer/schemata/index.md). For example, a {{ schema_ref('Person') }} has a {{ prop_ref('Person:nationality') }}, while a {{ schema_ref('Company') }} allows for setting a {{ prop_ref('LegalEntity:jurisdiction') }} (Both properties, however, have the same property type, {{ type_ref('country') }}).

## References

Entities can reference other entities. This is achieved via a special property type, `entity`. Properties of this type simply store the ID of another entity. For example, a {{ schema_ref('Passport') }} entity can be linked to a {{ schema_ref('Person') }} entity via its {{ prop_ref('Identification:holder') }} property:

```json
{
  "id": "passport-entity-id",
  "schema": "Passport",
  "properties": {
    "holder": ["person-entity-id"],
    "number": ["CJ 7261817"]
  }
}
```

!!! info
    Applications using FtM data usually need to resolve references bi-directionally. In the context of the example above, they will need to access the person based on it's ID in order to follow the holder link, but also query an inverted index to retrieve all the passports which reference a given person.

    In Aleph this is achieved using ElasticSearch and exposed via the `/api/2/entities/<id>/expand` API endpoint.

### Interstitial entities

A link between two entities will have its own attributes. For example, an investigator looking at a person that owns a company might want to know when that interest was acquired, and also what percentage of shares the person holds.

This is addressed by making interstitial entities. In the example above, an {{ schema_ref('Ownership') }} entity would be created, with references to the person as its owner property and to the company as its asset property. That entity can then define further properties, including {{ prop_ref('Interval:startDate') }} and {{ prop_ref('Ownership:percentage') }}:

```json
{
  "id": "ownership-entity-id",
  "schema": "Ownership",
  "properties": {
    "owner": ["person-entity-id"],
    "asset": ["company-entity-id"],
    "startDate": ["2020-01-01"],
    "percentage": ["51%"]
  }
}
```

!!! warning
    It is tempting to simplify this model by assuming that entities derived from {{ schema_ref('Thing') }} are node entities, and those derived from {{ schema_ref('Interval') }} are edges. This assumption is false and will lead to nasty bugs in your code.

## Streams

Many tools in the FtM ecosystem use streams of entities to transfer or store information. Entity streams are sequences of entity objects serialized to JSON as single lines without indentation, separated by newlines.

Entity streams are read and produced by virtually every part of the [CLI](cli.md), by the OpenAleph API, and by ingestors. When stored to disk, use the extensions `.ftm` or `.ijson`. The writer emits `id` as the first key on every line, so a plain `sort` orders the stream by entity ID — this property is what makes [sort-based aggregation](cli.md#aggregating-fragments) practical on datasets larger than memory.

## Entity representations

In the Python library, the same data model can be manipulated through two entity classes with different tradeoffs:

- [`ValueEntity`][followthemoney.entity.ValueEntity] stores property values as flat lists of strings. Dataset membership, first-seen, and last-seen timestamps live as entity-level fields. This is the default representation for most workflows — streaming, aggregation, exports, display — and it is what the [`ftm`](cli.md) CLI emits and consumes.
- [`StatementEntity`][followthemoney.statement.entity.StatementEntity] stores each property value as an individual [statement](statements.md), carrying per-value provenance: which dataset it came from, when it was first and last seen, the original unnormalized text, the language, and the statement origin within the pipeline. A `StatementEntity` can be unrolled into its constituent statements and reassembled from them, which is what enables canonical-ID deduplication and file-based entity aggregation over huge datasets.

Use `ValueEntity` by default. Reach for `StatementEntity` when the pipeline needs to retain per-value provenance (data journalism, sanctions lists with multiple source attributions), when building crawlers that integrate many overlapping sources, or when working with systems — like [`nomenklatura`](https://github.com/opensanctions/nomenklatura) — that deduplicate by assigning canonical IDs across source entities.

Both classes derive from `EntityProxy` and share the same property access API (`add()`, `get()`, `pop()`, `iterprops()`, `schema`, `id`). `EntityProxy` itself is being phased out as a direct dependency — new code should subclass or instantiate `ValueEntity` or `StatementEntity` rather than `EntityProxy`.
