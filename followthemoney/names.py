"""Project an FTM entity onto rigour's name-analysis engine.

`entity_names` turns an FtM entity into a set of rigour `Name` objects,
with structural part annotations applied from the entity's properties.

`schema_type_tag` and `PART_TAG_PROPS` stay exported for callers that
bypass `entity_names` (tests, experiments).
"""


from rigour.names import Name, NamePartTag, NameTypeTag, analyze_names

from followthemoney.proxy import EntityProxy
from followthemoney.schema import Schema
from followthemoney.types import registry


# Property → structural part annotation(s). A property can map to
# multiple tags for genuinely ambiguous cases: `fatherName` /
# `motherName` tag both MIDDLE (Slavic patronymic convention, sitting
# between given and family) and FAMILY (Hispanic convention, where the
# parent's name is an additional family name). Tagging both lets the
# downstream matcher align whichever slot actually fires against the
# other side — no locale detection needed, no crawler choice forced.
#
# `secondName` is deliberately collapsed to MIDDLE (not FAMILY) to
# match historical behaviour; some datasets use it for a second given
# name, others for a second surname. Do not change without a migration.
PART_TAG_PROPS: tuple[tuple[str, tuple[NamePartTag, ...]], ...] = (
    ("firstName", (NamePartTag.GIVEN,)),
    ("lastName", (NamePartTag.FAMILY,)),
    ("secondName", (NamePartTag.MIDDLE,)),
    ("middleName", (NamePartTag.MIDDLE,)),
    ("fatherName", (NamePartTag.MIDDLE, NamePartTag.FAMILY)),
    ("motherName", (NamePartTag.MIDDLE, NamePartTag.FAMILY)),
    ("title", (NamePartTag.HONORIFIC,)),
    ("nameSuffix", (NamePartTag.SUFFIX,)),
    ("weakAlias", (NamePartTag.NICK,)),
)


def schema_type_tag(schema: Schema) -> NameTypeTag:
    """Return the [NameTypeTag][rigour.names.NameTypeTag] for a schema.

    Args:
        schema: Any FTM schema.

    Returns:
        `PER`, `ORG`, `ENT`, `OBJ`, or `UNK` depending on the
        schema's position in the hierarchy.
    """
    if schema.is_a("Person"):
        return NameTypeTag.PER
    elif schema.is_a("Organization"):
        return NameTypeTag.ORG
    elif schema.is_a("LegalEntity"):
        return NameTypeTag.ENT
    elif schema.name in ("Vessel", "Asset", "Airplane", "Security"):
        return NameTypeTag.OBJ
    else:
        return NameTypeTag.UNK


def entity_names(
    entity: EntityProxy,
    props: tuple[str, ...] | None = None,
    *,
    matchable: bool = True,
    infer_initials: bool = False,
    symbols: bool = True,
    phonetics: bool = True,
    numerics: bool = True,
    consolidate: bool = True,
) -> set[Name]:
    """Build tagged rigour `Name` objects from an FTM entity.

    Args:
        entity: Any FTM entity (`ValueEntity` or `StatementEntity`).
        props: Property names that feed the primary name pool. `None`
            (default) takes all name-typed properties off the entity,
            honouring `matchable`.
        matchable: `True` (default) restricts the name properties used
            to those marked `matchable` in the schema.
        infer_initials: When `True`, every single-character latin
            name part is tagged with an `INITIAL` symbol — query-
            side behaviour, where `"J Smith"` arrives without a
            label on `"J"`. Default `False`; indexers and the
            candidate side of a matcher leave it at the default.
            Ignored for non-person names. No-op when `symbols`
            is `False`.
        symbols: Master switch for symbol emission. `True`
            (default) runs the tagger's match-and-apply pass and
            the INITIAL / NUMERIC emitters. `False` suppresses all
            symbols (`name.symbols` and `name.spans` stay empty);
            `part_tags` and structural `NamePartTag` labelling
            still apply.
        phonetics: When `True` (default), each `NamePart.metaphone`
            is populated. Callers that feed `part.metaphone` into
            downstream fields (e.g. yente's `name_phonemes` ES
            field) keep the default; callers that never read the
            property can pass `False` to skip the computation.
        numerics: When `True` (default), numeric-looking name parts
            that the tagger's ordinal list didn't cover pick up a
            `Symbol(NUMERIC, int_value)`. `False` keeps the cheaper
            `NamePartTag.NUM` structural annotation but drops the
            symbol — use when numeric-symbol overlap isn't part of
            downstream scoring.
        consolidate: When `True` (default), short names that are
            substrings of longer names in the result are dropped.
            **Indexers should pass `False`** to preserve partial-
            name recall (so `"John Smith"` can still match
            `"John K Smith"` from the other side).

    Returns:
        A de-duplicated set of tagged `Name` objects.
    """
    type_tag = schema_type_tag(entity.schema)

    if props is None:
        names: list[str] = entity.get_type_values(registry.name, matchable=matchable)
    else:
        names = []
        for prop in props:
            names.extend(entity.get(prop, quiet=True))

    part_tags: dict[NamePartTag, list[str]] = {}
    for prop, tags in PART_TAG_PROPS:
        values = entity.get(prop, quiet=True)
        if len(values) == 0:
            continue
        for tag in tags:
            part_tags.setdefault(tag, []).extend(values)

    return analyze_names(
        type_tag,
        names,
        part_tags,
        infer_initials=infer_initials,
        symbols=symbols,
        phonetics=phonetics,
        numerics=numerics,
        consolidate=consolidate,
    )
