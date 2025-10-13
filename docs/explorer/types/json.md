{% set type = select_type('json') %}
# {{ type.plural }}

This was a bad idea. Wrapping JSON objects into property values is a way of escaping the semantics of the FtM data model.

{% include 'templates/type.md' %}
