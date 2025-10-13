{% set type = select_type('address') %}
# {{ type.plural }}

{% include 'templates/type.md' %}

## Python API

::: followthemoney.types.AddressType
    options:
        heading_level: 3