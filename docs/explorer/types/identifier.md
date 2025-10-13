{% set type = select_type('identifier') %}
# {{ type.plural }}

Used for registration numbers and other codes assigned by an authority to identify an entity. This might include tax identifiers and statistical codes.

{% include 'templates/type.md' %}

## Identifier formats

Identifier properties can specify a `format`, which names a more precise validation mechanism for values assigned to these properties. The validators will enforce constraints on value length or use a checksum mechanism (as defined in [rigour.ids][]). Some identifiers are considered as `strong`, meaning they are part of a well-defined, often global, numbering scheme.

| Code | Label | Strong | Description | 
| ---- | ----- | ------ | ----------- |
{%- for fmt in rigour_id_formats %}
| `{{ fmt.names | join(", ") }}` | {{fmt.title}} |  {{ bool_icon(fmt.strong) }} | {{ fmt.description }} |
{%- endfor -%}

## Python API

::: followthemoney.types.IdentifierType
    options:
        heading_level: 3
