{% set type = select_type('gender') %}
# {{ type.plural }}

A human gender. This is not meant to be a comprehensive model of the social realities of gender but a way to capture data from (mostly) government databases and represent it in a way that can be used by structured data processing tools.

{% include 'templates/type.md' %}

## Data reference

| Code | Label |
| ---- | ----- |
| `other` | Other genders |
| `female` | Female |
| `male` | Male |


## Python API

::: followthemoney.types.GenderType
    options:
        heading_level: 3
