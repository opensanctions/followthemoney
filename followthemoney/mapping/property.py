import re
from copy import deepcopy
from typing import TYPE_CHECKING, Any, cast
from warnings import warn

from banal import as_bool, keys_values
from normality import stringify

from followthemoney.exc import InvalidMapping
from followthemoney.helpers import inline_names
from followthemoney.mapping.source import Record
from followthemoney.property import Property
from followthemoney.proxy import EntityProxy
from followthemoney.util import sanitize_text

if TYPE_CHECKING:
    from followthemoney.mapping.query import QueryMapping


class PropertyMapping:
    """Map values from a given record (e.g. a CSV row or SQL result) to the
    schema form."""

    __slots__ = (
        "entity",
        "format",
        "fuzzy",
        "join",
        "literals",
        "prop",
        "query",
        "refs",
        "replacements",
        "required",
        "split",
        "template",
    )

    FORMAT_PATTERN = re.compile("{{([^(}})]*)}}")

    def __init__(
        self, query: "QueryMapping", data: dict[str, Any], prop: Property
    ) -> None:
        self.query = query
        data = deepcopy(data)
        self.prop = prop

        self.refs = cast(list[str], keys_values(data, "column", "columns"))
        self.join = cast(str | None, data.pop("join", None))
        self.split = cast(str | None, data.pop("split", None))
        self.entity = stringify(data.pop("entity", None))
        self.format = stringify(data.pop("format", None))
        self.fuzzy = as_bool(data.pop("fuzzy", False))
        self.required = as_bool(data.pop("required", False))
        self.literals = cast(list[str], keys_values(data, "literal", "literals"))

        self.template = sanitize_text(data.pop("template", None))
        self.replacements: dict[str, str] = {}
        if self.template is not None:
            # this is hacky, trying to generate refs from template
            for ref in self.FORMAT_PATTERN.findall(self.template):
                self.refs.append(ref)
                self.replacements[f"{{{{{ref}}}}}"] = ref

    def bind(self) -> None:
        if self.prop.stub:
            raise InvalidMapping(f"Property for [{self.prop!r}] is a stub")

        if self.prop.deprecated:
            warn(
                f"Mapping uses a deprecated property: {self.prop!r}",
                DeprecationWarning,
                stacklevel=2,
            )

        if self.entity is None:
            return

        # Figure out if the schema types of the referenced entities
        # are of a type compatible with the range of this property.
        # For example, an asset can be owned by a legal entity, but
        # by a bank payment or a ship.
        for entity in self.query.entities:
            if entity.name != self.entity:
                continue
            if not self.prop.range or not entity.schema.is_a(self.prop.range):
                raise InvalidMapping(
                    f"The entity [{self.prop!r}] must be a {self.prop.range} (not {entity.schema.name})"
                )
            return

        raise InvalidMapping(f"No entity [{self.entity}] for property [{self.prop!r}]")

    def record_values(self, record: Record) -> list[str]:
        if self.template is not None:
            # replace mentions of any refs with the values present in the
            # current record
            value = self.template
            for repl, ref in self.replacements.items():
                ref_value = record.get(ref) or ""
                value = value.replace(repl, ref_value)
            return [value.strip()]

        values = list(self.literals)
        for ref in self.refs:
            rec_value = record.get(ref)
            if rec_value is not None:
                values.append(rec_value)
        return values

    def map(
        self, proxy: EntityProxy, record: Record, entities: dict[str, EntityProxy]
    ) -> list[str]:
        if self.entity is not None:
            entity = entities.get(self.entity)
            if entity is not None:
                proxy.unsafe_add(self.prop, entity.id, cleaned=True)
                inline_names(proxy, entity)
            return []

        # clean the values returned by the query, or by using literals, or
        # formats.
        values: list[str] = self.record_values(record)

        if self.join is not None:
            values = [self.join.join(values)]

        if self.split is not None:
            splote = []
            for value in values:
                splote.extend(value.split(self.split))
            values = splote

        discarded_values: list[str] = []

        for value in values:
            added_value = proxy.unsafe_add(
                prop=self.prop,
                value=value,
                fuzzy=self.fuzzy,
                format=self.format,
            )

            if value is not None and added_value is None:
                discarded_values.append(value)

        return discarded_values
