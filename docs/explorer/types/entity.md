{% set type = select_type('entity') %}
# {{ type.plural }}

{% include 'templates/type.md' %}

## Python API

::: followthemoney.types.EntityType
    options:
        heading_level: 3