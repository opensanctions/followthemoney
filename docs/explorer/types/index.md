# Property types

Each property in FtM has a type, which represents its semantic structure. Types are used for data validation, normalisation and to facilitate effective search for entities.

| Name | Label | Matchable | Pivot |
| ---- | ----- | --------- | ----- |
{% for type in registry.types | sort(attribute='name') %}| {{ type_ref(type.name) }} | {{ type.label }} | {{ bool_icon(type.matchable) }} | {{ bool_icon(type.pivot) }} |
{% endfor %}
