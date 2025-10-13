{% set schema = select_schema(page.title) %}

# {{ schema.label }}

{% if schema.deprecated %}
!!! warning "Deprecated"
    This schema is deprecated and will be removed in the next major version of FollowTheMoney. Don't use it when building new data pipelines.
{% endif %}

{% if schema.description %}
<div class="description">
{{ schema.description }}
</div>
{% endif %}

{% if schema.abstract %}
- `{{ schema.name }}` is an **abstract** schema and is used for inheritance only and shouldn’t be used directly.
{% endif %}
{% if schema.generated %}
- `{{ schema.name }}` is a **generated** schema and shouldn’t be created directly by users.
{% endif %}
{% if schema.matchable %}
- `{{ schema.name }}` is a **matchable** schema and can be used for matching and cross-referencing.
{% endif %}
{% if schema.hidden %}
- `{{ schema.name }}` is a **hidden** schema and shouldn’t be displayed in user interfaces or created by users.
{% endif %}

## Relations to other schemata 

`{{ schema.name }}` has the following relations to other schemata in the model:

| Relation | Schemata | 
| -------- | -------- |
| **Properties inherited from:** | {% if schema.extends | length() %}{% for s in schema.extends %}{{ schema_ref(s) }}<br>{% endfor %}{% else %}{{ NULL }}{% endif %} |
| **More precise schemata:** | {% if schema.descendants | length() %}{% for s in schema.descendants %}{{ schema_ref(s) }}<br>{% endfor %}{% else %}{{ NULL }}{% endif %} |
{%- if schema.matchable -%}
| **Matchable with:** | {% if schema.matchable_schemata | length() %}{% for s in schema.matchable_schemata %}{{ schema_ref(s) }}<br>{% endfor %}{% else %}{{ NULL }}{% endif %} |
{%- endif -%}


## Properties

**{{ schema.label }}** has multiple properties to describe its data. Some properties are inherited from its parent schemata.


??? Info "Icon legend"
    :material-closed-caption-outline: This property is used to compute a [caption][followthemoney.proxy.EntityProxy.caption] for the entity.

    :material-star-circle-outline: This property is a _featured_ property, which means in UI applications it should be shown with higher information hierarchy.

    :material-transit-connection-horizontal: This property is a _matchable_ property and can be used in matching systems to find similar entities.

    :material-eye-off: This property is a _hidden_ property and should not be rendered in UI applications.


| Name | Label | Type |
| ---- | ----- | ---- |
{% for prop in sorted_props(schema) %}| {{ prop_ref(prop) }}{ #{{ prop.name }} } {{ prop_caption_icon(prop) }} {{ prop_hidden_icon(prop) }} {{ prop_featured_icon(prop) }} {{ prop_matchable_icon(prop) }} | {{ prop.label }} {% if prop.description %}<br><em>{{ prop.description }}</em>{% endif %} | {{ type_ref(prop.type) }} |
{% endfor %}

## How to use it in a graph or timeline

FtM has well-defined semantics for different representations of entities, for example in a network graph or in a timeline.

{% if schema.edge %}
When using this schema in a [graph representation](/docs/graphs.md), it should be represented as an **edge**.
{% else %}
When using this schema in a [graph representation](/docs/graphs.md), it should be represented as a **node**.
{% endif %}

| Semantic | Property |
| -------- | -------- |
| Temporal start | {% if schema.temporal_start %}{% for prop in schema.temporal_start_props %}{{ prop_ref(prop) }}<br>{% endfor %}{% else %}{{ NULL }}{% endif %}|
| Temporal end | {% if schema.temporal_end %}{% for prop in schema.temporal_end_props %}{{ prop_ref(prop) }}<br>{% endfor %}{% else %}{{ NULL }}{% endif %}|
{% if schema.source_prop %}| Edge source | {{ prop_ref(schema.source_prop) }} |{% endif %}
{% if schema.target_prop %}| Edge target | {{ prop_ref(schema.target_prop) }} |{% endif %}
