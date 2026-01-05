from functools import cache
from typing import Tuple

from followthemoney.model import Model
from followthemoney.types import registry
from followthemoney.util import const

BASE_ID = "id"

# Some property types should not set the `lang` attribute on statements.
# These are typically non-linguistic types, although there's an argument
# that language metadata could be useful for dates and countries, where
# text parsing is likely to have taken place.
NON_LANG_TYPE_NAMES = {
    registry.entity.name,
    registry.date.name,
    registry.checksum.name,
    registry.email.name,
    registry.phone.name,
    registry.gender.name,
    registry.mimetype.name,
    registry.topic.name,
    registry.url.name,
    registry.country.name,
    registry.language.name,
    registry.ip.name,
    BASE_ID,
}


def pack_prop(schema: str, prop: str) -> str:
    return f"{schema}:{prop}"


@cache
def get_prop_type(schema: str, prop: str) -> str:
    if prop == BASE_ID:
        return BASE_ID
    schema_obj = Model.instance().get(schema)
    if schema_obj is None:
        raise TypeError("Schema not found: %s" % schema)
    prop_obj = schema_obj.get(prop)
    if prop_obj is None:
        raise TypeError("Property not found: %s" % prop)
    return prop_obj.type.name


@cache
def unpack_prop(id: str) -> Tuple[str, str, str]:
    schema, prop = id.split(":", 1)
    prop_type = get_prop_type(schema, prop)
    return const(schema), prop_type, const(prop)
