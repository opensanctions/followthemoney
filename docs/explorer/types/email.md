{% set type = select_type('email') %}
# {{ type.plural }}

{% include 'templates/type.md' %}

## Python API

::: followthemoney.types.EmailType
    options:
        heading_level: 3