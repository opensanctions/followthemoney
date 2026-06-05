---
description: Add a `riskSource` entity property on Thing (range Thing) that links a derived-risk entity back to the directly-designated entity its risk originates from, e.g. a subsidiary marked `sanction.control` pointing to the SDN at the top of an ownership chain.
date: 2026-06-05
tags: [schema, sanctions, ownership, risk, thing]
---

# `riskSource` property on `Thing`

## Why

The `sanction.control` topic (issue #247, PR #310) marks entities that are pulled
into sanctions scope by derivation — a subsidiary 50%-owned by a designated person,
a vessel owned by a blocked company — rather than by direct designation. The topic
records *that* an entity carries derived risk, but not *from whom*.

For a chain of ownership (a subsidiary of a subsidiary of an SDN), an analyst or a
compliance system needs to answer "why is this entity flagged?" without re-traversing
the ownership graph. `riskSource` is a denormalized pointer from the derived entity
back to the directly-designated entity its risk originates from.

This generalizes beyond sanctions: the same need exists for any member of the
`topics` `RISKS` set (debarment, export-control derivation, close-associate-by-PEP).
Hence the generic name `riskSource`, paired with the existing `topics` field, rather
than a sanctions-specific `sanctionSource`.

## What exists today

- Ownership relationships are modeled as first-class entities (`Ownership`,
  `Directorship`, `Associate`), connecting `owner`/`asset`, `director`/`organization`.
  These carry the *mechanism* (percentage, role, dates).
- `topics` (on `Thing`) carries the risk classification, including the new
  `sanction.control`.
- There is no flat edge from a derived entity to the entity that is the *source*
  of its risk. Answering "who made this risky" requires graph traversal over
  `Ownership`/`Directorship` intermediates.

`riskSource` does not replace the ownership graph — it is a derived shortcut that
records the *conclusion* of a 50%-rule analysis ("this entity's risk derives from
that SDN") alongside the underlying relationship that justifies it.

## Design

### The property

On `Thing`, mirroring the existing entity-pointer convention (`addressEntity`, `proof`):

```yaml
riskSource:
  label: Risk source
  description: "The directly-designated entity from which this entity's risk
    classification ultimately derives, e.g. the sanctioned person at the origin of an
    ownership chain. See also the `topics` property."
  # No reverse defined — deliberately. See "No reverse property" below.
  type: entity
  range: Thing
  matchable: false
```

`A riskSource B` reads "B is the source of A's risk." A is the derived entity
(subsidiary); B is the directly-designated entity at the origin of the chain.

### No reverse property (deliberate)

Unlike every other entity-pointer property in the model, `riskSource` defines **no
`reverse`**. This is the crux of the design, not an omission.

The inverse of `riskSource` is a **one-to-many hub fan-out**: a major sanctioned
conglomerate (think a state energy company with thousands of subsidiaries and board
members) is the `riskSource` of thousands of entities. A reverse property would
materialize all of them as inverted edges. The nested-targets exporter
(`zavod/exporters/nested.py` → `Entity.to_nested_dict` → `View.get_adjacent`) inlines
every adjacent entity at depth 1, so the hub's `targets.nested.json` object would
balloon with thousands of full entity dicts — largely *duplicating* the fan-out that
already exists via its `Ownership`/`Directorship` reverse edges.

The asymmetry is the point: `riskSource` is **many-to-few forward** (each entity has
one or a few ultimate sources) but **one-to-many reverse**. The forward direction is
bounded and safe to inline; the reverse is the explosion this property was built to
*avoid*. Re-introducing it via a reverse defeats the purpose.

Dropping the reverse resolves this at the schema level, with no changes to
nomenklatura or zavod: every store backend's `get_inverted` yields a reverse edge
only when `prop.reverse is not None`, and the same guard holds in yente's nested
search and the fragment exporter. `reverse` is `Optional` by design and the whole
stack already handles `None`; verified empirically that a 2,000-entity hub produces
zero inverted/adjacent results and that serialization, graph building, and model dump
are unaffected.

The trade-off: the cheap store-level inverse query "what is sanctioned because of X"
is no longer available — but that query *is* the pathological hub fan-out. It is
better served deliberately (filter `topics` + `riskSource == X` in search/SQL) than
by inline graph expansion.

### Settled

- **`matchable: false`** — confirmed. The `entity` type defaults to `matchable:
  True`, so this is set explicitly. `riskSource` is a provenance pointer, not an
  identity signal; it must not feed cross-referencing or scoring.

- **Direction: the ultimate designated entity, not the immediate parent.**
  `riskSource` exists to answer "which designation is responsible for this flag" in
  O(1). The immediate parent in an ownership chain is itself only a derived entity,
  so pointing at it just defers the question one hop and forces consumers (yente,
  the API, the UI) to re-traverse `riskSource` until they hit a base `sanction`
  topic — exactly the graph walk this denormalized pointer is meant to eliminate.
  The full ownership path is already first-class data (`Ownership`/`Directorship`
  edges), so `riskSource` does not need to re-encode it; its only value-add is the
  shortcut to the origin. The complexity of carrying the origin through iterative
  propagation is absorbed in the analyzer, not the schema (see "Populating", below).

- **`range: Thing`** — confirmed. Sources of sanctions risk are usually designated
  Persons/Organizations, but vessels, securities, and crypto wallets are also
  directly sanctioned and can be the origin of a derived flag, so the range stays
  broad rather than narrowing to `LegalEntity`.

- **No reverse property** — confirmed (see "No reverse property", above). An earlier
  draft proposed a `riskLinked` reverse; it was dropped to prevent hub fan-out in
  inverted/nested views.

### Multi-value is a feature, not a quirk

All FtM properties are `List[str]`, so `riskSource` is inherently multi-valued. This
is semantically correct here: under OFAC/EU aggregation, an entity can be 50%-owned
in aggregate by *several* SDNs (30% + 25%). Such an entity legitimately has multiple
risk sources, and the property records all of them.

## Implementation steps

1. **Schema** — add the `riskSource` block to `followthemoney/schema/Thing.yaml`
   (after `proof`, alongside the other entity-pointer properties).
2. **Regenerate generated artifacts** — `make default-model`, which runs
   `ftm dump-model` into `js/src/defaultModel.json` and
   `java/src/main/resources/defaultModel.json`, then `contrib/gen_docs.py`. No reverse
   stub is generated.
3. **Translations** — `make translate` (`pybabel extract`) to add the new label
   strings to the catalog; translation across locales is a follow-up, not a blocker.
4. **Tests** — assert the schema loads, `model.get("Thing").get("riskSource")`
   resolves with `range == Thing` and `matchable is False`, and that `prop.reverse is
   None` (no `riskLinked` stub on `Thing`). Mirror existing entity-property tests.

## Downstream impact

- **No migration.** Additive, optional property. Does not touch ID generation,
  `compute_key`, or checksums — the stability constraints are not engaged.
- **Namespacing: automatic.** `Namespace.apply()` rewrites every `entity`-type
  property value (`namespace.py:104-110`); `riskSource` references are signed/
  rewritten like any other entity reference with no special handling.
- **Matching:** with `matchable: false`, `riskSource` is ignored by comparison/
  scoring — intended.
- **yente / API:** the property is exposed automatically via the model; no code
  change needed.
- **Nested / inverted views:** with no reverse, hub entities accumulate no inverted
  `riskSource` edges, so `nested.py` and yente nested search are unaffected (see "No
  reverse property", above).
- **JS / Java consumers:** pick up the property from the regenerated `defaultModel.json`.

## Populating `riskSource` (out of scope — opensanctions repo)

The value is produced by the `ann_graph_topics` analyzer
(`datasets/_analysis/ann_graph_topics/analyzer.py`), which walks the
ownership/relationship graph and propagates risk topics one hop per run. Its
`emit_patch(context, risk_source, related_entity, topic, ...)` helper already
receives an originating entity as `risk_source` and currently writes only the
`topics` value onto the `related_entity` patch.

Adding the pointer is `patch.add("riskSource", source.id)` in `emit_patch` — but
`source` must be the *ultimate* designated entity, not the node currently being
analyzed. Because the analyzer is iterative (an entity tagged in one run becomes a
`risk_source` for its downstream assets in the next), the node in hand is often
itself a derived entity. Resolve the origin before emitting: a node carrying the
base `sanction` topic *is* the source; a node that is only derived forwards the
`riskSource` it already carries. Sketch:

```python
source = entity if "sanction" in non_graph_topics(context, entity) \
    else entity.get("riskSource")
emit_patch(context, source, related_entity, topic, ...)
```

This keeps the hop-by-hop topic propagation unchanged and only resolves the recorded
source to the origin. Aggregation falls out naturally: an entity owned by two SDNs
ends up with two `riskSource` values. Wiring `sanction.control` into the analyzer's
tagging rules is itself separate work; this plan only adds the FtM schema slot.

## Also out of scope

- **UI treatment** in Aleph / opensanctions.org for displaying the derived-risk link.
- **Backfill** of `riskSource` onto already-emitted derived-risk entities.
