from rigour.names import NamePartTag, NameTypeTag

from followthemoney.schema import Schema


# Define the mapping of property names to name part tags.
# This is used to tag the parts of the name with their type by using
# `Name.tag_text` with the value of the property to mark name parts.
PROP_PART_TAGS = (
    ("firstName", NamePartTag.GIVEN),
    ("lastName", NamePartTag.FAMILY),
    ("secondName", NamePartTag.MIDDLE),
    ("middleName", NamePartTag.MIDDLE),
    ("fatherName", NamePartTag.PATRONYMIC),
    ("motherName", NamePartTag.MATRONYMIC),
    ("title", NamePartTag.HONORIFIC),
    ("nameSuffix", NamePartTag.SUFFIX),
    ("weakAlias", NamePartTag.NICK),
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
