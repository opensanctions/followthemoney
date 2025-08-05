# Entity schemata

Explore the default data model shipped with FollowTheMoney. It includes {{ model.schemata | length }} schemata, focussed on the domain of financial crime, corruption investigations, and document forensics.

| Name | Label | Abstract | Generated | Matchable | Hidden |
| ---- | ----- | -------- | --------- | --------- | ------ |
{% for schema in model.schemata.values() | sort(attribute='label') %}| {{ schema_ref(schema.name) }} | {{ schema.label }} | {{ bool_icon(schema.abstract) }} | {{ bool_icon(schema.generated) }} | {{ bool_icon(schema.matchable) }} | {{ bool_icon(schema.hidden) }} |
{% endfor %}
