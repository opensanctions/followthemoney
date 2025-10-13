{% set type = select_type('mimetype') %}
# {{ type.plural }}

A MIME media type are a specification of a content type on a network. Each MIME type is assigned by IANA and consists of two parts: the type and sub-type. Common examples are: `text/plain`, `application/json` and `application/pdf`.

{% include 'templates/type.md' %}

## Well-known MIME types

| Code | Label |
| ---- | ----- |
{%- for code, label in rigour_mime_types.items() %}
| `{{code}}` | {{label}} |
{%- endfor -%}

## Python API

::: followthemoney.types.MimeType
    options:
        heading_level: 3
