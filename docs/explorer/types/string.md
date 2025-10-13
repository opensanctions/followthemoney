{% set type = select_type('string') %}
# {{ type.plural }}

String type properties are used for short descriptive text, such as a sector classification. For longer narrative descriptions, the type {{ type_ref('text') }} is used.

{% include 'templates/type.md' %}


## Python API

::: followthemoney.types.StringType
    options:
        heading_level: 3