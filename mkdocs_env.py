from typing import Any, Generator, Set
from rigour.mime.types import LABELS
from rigour.territories import get_territories
from rigour.ids import get_identifier_formats
from followthemoney import model, __version__
from followthemoney import registry
from followthemoney.property import Property
from followthemoney.schema import Schema
from followthemoney.types.common import PropertyType


def define_env(env):
    """
    This is the hook for the variables, macros and filters.
    """

    env.variables["model"] = model
    env.variables["registry"] = registry
    env.variables["ftm_version"] = __version__
    env.variables["rigour_mime_types"] = LABELS
    env.variables["rigour_territories"] = get_territories()
    env.variables["rigour_id_formats"] = get_identifier_formats()
    env.variables["risk_topics"] = registry.topic.RISKS
    env.variables["NULL"] = "-"

    @env.macro
    def bool_icon(val: bool) -> str:
        if val:
            return ":material-check:"
        return ":material-close:"

    @env.macro
    def prop_hidden_icon(prop: Property) -> str:
        if prop.hidden:
            return ":material-eye-off:"
        return ""

    @env.macro
    def prop_featured_icon(prop: Property) -> str:
        if prop.name in prop.schema.featured:
            return ":material-star-circle-outline:"
        return ""

    @env.macro
    def prop_matchable_icon(prop: Property) -> str:
        if prop.matchable:
            return ":material-transit-connection-horizontal:"
        return ""

    @env.macro
    def prop_caption_icon(prop: Property) -> str:
        if prop.name in prop.schema.caption:
            return ":material-closed-caption-outline:"
        return ""

    @env.macro
    def doc_string(val: Any) -> str:
        return val.__doc__ or ""

    @env.macro
    def schema_ref(schema: Schema | str) -> str:
        if isinstance(schema, Schema):
            schema = schema.name
        return f"[`{schema}`](/explorer/schemata/{schema}.md)"

    @env.macro
    def type_ref(type_: PropertyType | str) -> str:
        return f"[`{type_}`](/explorer/types/{type_}.md)"

    @env.macro
    def prop_ref(prop: Property | str) -> str:
        if isinstance(prop, Property):
            schema, name = prop.schema.name, prop.name
        else:
            schema, name = prop.split(":")
        qname = ":".join((schema, name))
        return f"[`{qname}`](/explorer/schemata/{schema}.md#{name})"

    @env.macro
    def select_schema(name: str) -> Schema:
        s = model.get(name)
        assert s is not None, f"Schema not in model: `{name}`"
        return s

    @env.macro
    def select_type(name: str) -> PropertyType:
        t = registry.get(name)
        assert t is not None, f"Property type not in model: `{name}`"
        return t

    @env.macro
    def sorted_props(schema: Schema) -> Generator[Property, None, None]:
        """Sort properties by featured, required, own schema, other schemata"""
        seen: Set[str] = set()
        for prop in schema.caption:
            seen.add(prop)
            yield schema.properties[prop]
        for prop in schema.featured:
            if prop not in seen:
                seen.add(prop)
                yield schema.properties[prop]
        for prop in schema.required:
            if prop not in seen:
                seen.add(prop)
                yield schema.properties[prop]
        for prop in schema.properties.values():
            if prop.name not in seen:
                seen.add(prop.name)
                yield prop
