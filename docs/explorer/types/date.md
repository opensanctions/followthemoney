{% set type = select_type('date') %}
# {{ type.plural }}

Dates are given in a basic ISO 8601 date or date-time format, `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`.

In source data, we find varying degrees of precision: some events may be defined as a full timestamp (`2021-08-25T09:26:11`), while for many we only know a year (`2021`) or month (`2021-08`). Such date prefixes are carried through and used to specify date precision as well as the actual value.

In the future, FtM may include support for approximate dates (`~1968`), and date ranges (`1968-03 -- 1973-01`).

{% include 'templates/type.md' %}

## Temporal extent

Many [schema](../schemata/index.md) include annotations that select properties which define the temporal start and end information for a given entity type: for example, an {{schema_ref('Ownership')}} may have a `startDate` and `endDate`, a {{schema_ref('Company')}} a `incorporationDate` and `dissolutionDate`, and a {{schema_ref('Person')}} a `birthDate` and `deathDate`.

Temporal extents are meant to provide semantics that help to project entity information into timelines.

## Python API

Date validation and handling in Python is performed using the [prefixdate](https://github.com/pudo/prefixdate) Python library, which may eventually be subsumed in `rigour`.

::: followthemoney.types.DateType
    options:
        heading_level: 3