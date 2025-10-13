{% set type = select_type('text') %}
# {{ type.plural }}

Text type properties are used for long, textual documentation attached to entities, such as the {{ prop_ref('Document:bodyText') }} of a {{ schema_ref('Document' )}} or the {{ prop_ref('Thing:notes') }} describing a {{ schema_ref('Thing' )}}.

Backends should use full search text indexing to handle text fields.

{% include 'templates/type.md' %}

## Python API

::: followthemoney.types.TextType
    options:
        heading_level: 3