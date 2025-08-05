---
hide:
  - toc
---

{% set type = select_type('country') %}
# {{ type.plural }}

FtM's model of political geography is an evolving part of the toolkit. The model has now matured to distinguish several concepts:

* **Territories** are units of political geography. They can overlap or contradict each other in terms of the physical space they occupy. As long as someone claims to hold political power in a place, this can be reason for FtM to model it.
* **Jurisdictions** are territories which impose their own legal regime, often with regards to the formation of companies. Most countries are jurisdictions, but some countries are subdivided into smaller jurisdictions - think Dubai as part of the UAE, Delaware as part of the US.
* **Countries** are UN member states. Beyond that, certain territories are countries in practice (think Kosovo). To go with the old adage, a country is a territory [with an army and a navy](https://en.wikipedia.org/wiki/A_language_is_a_dialect_with_an_army_and_navy).

After first modeling UN member states as *countries*, the supported codelist quickly grew to include contested territories and breakaway regions for practical reasons. Referencing controversial places (and the people who govern them) is a key feature of FtM data.

If the presence of a country in this list is offensive to you, we invite you to reflect on the mental health impact of being angry at tables on the internet.


{% include 'templates/type.md' %}

## Territories

This table lists the full set of geographic territories described in `rigour`. A subset of them are currently supported as property values in FtM, with the rest being mapped to existing country codes as stated here. This table is the return value of [rigour.territories.get_territories][]. The returned objects also provides alternate codes and Wikidata QIDs for some territories, expanding the ability to interpret data from a wide range of sources.

| Code | Label | FtM | Country | Jurisdiction | Historical | Wikidata |
| ---- | ----- | --- | ------- | ------------ | ---------- | -------- |
{%- for terr in rigour_territories %}
| `{{terr.code}}` | {{terr.name}} | `{{ terr.ftm_country }}` | {{ bool_icon(terr.is_country) }} | {{ bool_icon(terr.is_jurisdiction) }} | {{ bool_icon(terr.is_historical) }} | [`{{ terr.qid }}`](https://www.wikidata.org/wiki/{{terr.qid}}) |
{%- endfor -%}

## Python API

::: followthemoney.types.CountryType
    options:
        heading_level: 3
