# followthemoney

FtM is a data model and toolkit for anti-money laundering and sanctions data. It processes millions of entities, so performance matters throughout.

## Key modules

- `proxy.py` — `EntityProxy`, base entity class (being phased out in favour of the two subtypes below)
- `entity.py` — `ValueEntity(EntityProxy)`, lightweight entity with dataset/temporal metadata
- `statement/entity.py` — `StatementEntity(EntityProxy)`, entity backed by per-claim statements
- `schema.py` / `schema/` — schema definitions and hierarchy (YAML + runtime)
- `property.py` — property definitions on schemata
- `types/` — property type system (name, date, country, phone, etc.)
- `model.py` — singleton `Model` registry, loads all schemata
- `dataset/` — dataset metadata, catalogs, collections, query DSL
- `statement/` — statement-level data model (per-claim granularity)
- `compare.py` — entity similarity scoring
- `namespace.py` — entity ID namespacing and signing

Docs: https://followthemoney.tech ([source](docs/))

## Build & test

- `make test` — run pytest
- `make typecheck` — run mypy --strict

## Code conventions

**Type safety** (mypy --strict enforced):
- All functions must have full type annotations including return types
- Forward references: use quoted strings (`"DataCatalog[DS]"`), not `from __future__ import annotations`
- Use `TYPE_CHECKING` blocks for circular imports

**Explicitness**:
- None checks: `if x is None`, never `if not x`
- Collection emptiness: `if len(x) == 0`, not `if not x`
- No bare except clauses

**Performance** (code runs on millions of entities):
- Use `__slots__` on data classes in hot paths
- Use `@cache` / `@cached_property` for immutable computations
- Prefer generators (yield) over materializing lists
- Use sets for membership testing and deduplication
- In tight loops: `type(x) is str` over `isinstance(x, str)`
- Don't add abstraction layers to hot paths; inline when the code explains why

**Style**:
- Absolute imports only, no relative imports
- f-strings preferred; % formatting acceptable in error/exception messages
- Docstrings on classes and modules; omit on trivial functions. Explain the *why*, not the *how*
- Subject/context argument first, then operation (e.g. `evaluate_query(catalog, query)`)

## Data model essentials

- **All property values are `List[str]`** — even numbers, dates, booleans. The type system cleans on input and interprets on output. Don't store native Python types.
- **Schema inheritance is multi-rooted** — a schema can extend multiple parents (e.g. `Company` extends both `Organization` and `Asset`). This affects property resolution and `is_a` checks.
- **Type cleaning delegates to `rigour` and `normality`** — phone parsing, name normalization, country codes, identifier validation, etc. Don't reimplement what these libraries already provide.
- **Property types are singletons** — access via `registry.phone`, `registry.name`, etc. (from `followthemoney.types`), not by instantiating `PropertyType` directly.
- **`cleaned=True` skips validation** — `EntityProxy.__init__` and `add()` accept a `cleaned` flag that bypasses type cleaning. Used for trusted/pre-validated data in hot paths. Only use when the data is already normalized.
- **"territory" over "country"** — we're migrating from "country" to "territory" in new code and non-breaking contexts. Territories are a superset (includes disputed regions, supranational entities, etc.).
