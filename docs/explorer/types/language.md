{% set type = select_type('language') %}
# {{ type.plural }}

A human written or spoken language, defined by an `ISO-639` three-letter code. This list is arbitrarily limited for some weird upstream technical reasons, but we'll happily accept pull requests for additional languages once there is a specific need for them to be supported.

Additional values can be introduced in FtM type enumerations within minor releases.

{% include 'templates/type.md' %}

## Data reference

| Code | Label |
| ---- | ----- |
{%- for code, label in select_type('language').names.items() %}
| `{{code}}` | {{label}} |
{%- endfor -%}



## Python API

::: followthemoney.types.LanguageType
    options:
        heading_level: 3
