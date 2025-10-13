{% set type = select_type('checksum') %}
# {{ type.plural }}

{% include 'templates/type.md' %}

## Python API

::: followthemoney.types.ChecksumType
    options:
        heading_level: 3