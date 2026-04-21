"""Project an FTM entity onto rigour's name-analysis engine.

`entity_names` turns an FtM entity into a set of rigour `Name` objects,
with structural part annotations applied from the entity's properties.

`schema_type_tag` and `PART_TAG_PROPS` stay exported for callers that
bypass `entity_names` (tests, experiments).
"""

from typing import Dict, List, Optional, Set, Tuple

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
PART_TAG_PROPS: Tuple[Tuple[str, Tuple[NamePartTag, ...]], ...] = (
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
    """Return the name type tag for the given schema."""
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
    props: Optional[Tuple[str, ...]] = None,
    *,
    matchable: bool = True,
    infer_initials: bool = False,
    phonetics: bool = True,
    numerics: bool = True,
    consolidate: bool = True,
) -> Set[Name]:
    """Build tagged rigour `Name` objects from an FTM entity.

    Used by matchers (nomenklatura) and indexers (yente) to get a
    uniform set of `Name` objects for an entity, with structural
    part annotations already applied. Flags forward to
    `rigour.names.analyze_names`; see its docstring for their
    semantics.

    `props` selects which properties feed the primary name pool.
    `None` (default) takes all name-typed properties off the entity,
    honouring `matchable`. An explicit tuple bypasses the `matchable`
    filter and reads exactly those props. Tuple (not list) so the
    signature stays hashable for the surrounding `lru_cache`.

    `matchable=True` (default) restricts to `name`, `alias`,
    `previousName`. `matchable=False` additionally pulls in the
    non-matchable name-typed properties — `weakAlias` and
    `abbreviation` — as standalone names.

    `PART_TAG_PROPS` always runs regardless of `props` / `matchable`
    — structural annotations from `firstName`, `lastName`,
    `fatherName`, … are orthogonal to the main-name pool.
    """
    type_tag = schema_type_tag(entity.schema)

    if props is None:
        names: List[str] = entity.get_type_values(registry.name, matchable=matchable)
    else:
        names = []
        for prop in props:
            names.extend(entity.get(prop, quiet=True))

    part_tags: Dict[NamePartTag, List[str]] = {}
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
        phonetics=phonetics,
        numerics=numerics,
        consolidate=consolidate,
    )
