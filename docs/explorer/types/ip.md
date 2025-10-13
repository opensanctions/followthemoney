{% set type = select_type('ip') %}
# {{ type.plural }}

{% include 'templates/type.md' %}

## Python API

::: followthemoney.types.HTMLType
    options:
        heading_level: 3
