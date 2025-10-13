{% set type = select_type('number') %}
# {{ type.plural }}

Numeric data is usually stored in FtM for descriptive reasons more than to facilitate quantitative analysis. The `number` type reflects this. Stored as strings, FtM numbers can consist of a `value` and a `unit`, e.g. `37 %` or `9 t`. Numbers are expected to use a `.` as their decimals separator; a `,` separator can be introduced to group thousands, lakhs or crores (they're removed for storage).

Some unit strings (including for area and currency) are normalized using [rigour.units.normalize_unit][] (e.g. `sqm` -> `m²`).

{% include 'templates/type.md' %}

## Python API

::: followthemoney.types.NumberType
    options:
        heading_level: 3
