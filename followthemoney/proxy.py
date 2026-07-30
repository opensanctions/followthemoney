import builtins
import hashlib
import logging
from collections.abc import Generator, Iterable
from itertools import product
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast

from banal import ensure_dict
from rigour.names import pick_name

from followthemoney.exc import InvalidData
from followthemoney.model import Model
from followthemoney.property import Property
from followthemoney.schema import Schema
from followthemoney.types import registry
from followthemoney.types.common import PropertyType
from followthemoney.util import (
    HASH_ENCODING,
    gettext,
    make_entity_id,
    merge_context,
    sanitize_text,
)
from followthemoney.value import Values, string_list

if TYPE_CHECKING:
    from hashlib import _Hash

log = logging.getLogger(__name__)
P = Property | str
E = TypeVar("E", bound="EntityProxy")


class EntityProxy:
    """A wrapper object for an entity, with utility functions for the
    introspection and manipulation of its properties.

    This is the main working object in the library, used to generate, validate
    and emit data."""

    __slots__ = ["_properties", "_size", "context", "id", "key_prefix", "schema"]

    def __init__(
        self,
        schema: Schema,
        data: dict[str, Any],
        key_prefix: str | None = None,
        cleaned: bool = True,
    ):
        data = dict(data or {})
        properties = data.pop("properties", {})
        if not cleaned:
            properties = ensure_dict(properties)

        #: The schema definition for this entity, which implies the properties
        #: That can be set on it.
        self.schema = schema

        #: When using :meth:`~make_id` to generate a natural key for this entity,
        #: the prefix will be added to the ID as a salt to make it easier to keep
        #: IDs unique across datasets. This is somewhat redundant following the
        #: introduction of :class:`~followthemoney.namespace.Namespace`.
        self.key_prefix = key_prefix

        #: A unique identifier for this entity, usually a hashed natural key,
        #: a UUID, or a very simple slug. Can be signed using a
        #: :class:`~followthemoney.namespace.Namespace`.
        self.id = str(data["id"]) if data.get("id") else None
        if not cleaned:
            self.id = sanitize_text(self.id)

        #: If the input dictionary for the entity proxy contains fields other
        #: than ``id``, ``schema`` or ``properties``, they will be kept in here
        #: and re-added upon serialization.
        self.context = data
        self._properties: dict[str, list[str]] = {}
        self._size = 0

        for key, values in properties.items():
            if key not in self.schema.properties:
                continue
            if cleaned:
                # This does not call `self.add` as it might be called millions of times
                # in some context and we want to avoid the performance overhead of
                # doing so.
                seen: set[str] = set()
                seen_add = seen.add
                unique_values = [v for v in values if not (v in seen or seen_add(v))]
                self._properties[key] = unique_values
                self._size += sum([len(v) for v in unique_values])
            else:
                self.add(key, values, quiet=True)

    def make_id(self, *parts: Any) -> str | None:
        """Generate a (hopefully unique) ID for the given entity, composed
        of the given components, and the :attr:`~key_prefix` defined in
        the proxy.
        """
        self.id = make_entity_id(*parts, key_prefix=self.key_prefix)
        return self.id

    def _prop_name(self, prop: P, quiet: bool = False) -> str | None:
        # This is pretty unwound because it gets called a *lot*.
        if prop in self.schema.properties:
            return cast(str, prop)
        try:
            obj = cast(Property, prop)
            if obj.name in self.schema.properties:
                return obj.name
        except AttributeError:
            pass
        if quiet:
            return None
        msg = gettext("Unknown property (%s): %s")
        raise InvalidData(msg % (self.schema, prop))

    def get(self, prop: P, quiet: bool = False) -> list[str]:
        """Get all values of a property.

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :param quiet: a reference to an non-existent property will return
            an empty list instead of raising an error.
        :return: A list of values.
        """
        if prop in self.schema.properties:
            return self._properties.get(prop, [])  # type: ignore

        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None:
            return []
        return self._properties.get(prop_name, [])

    def get_prop(self, prop: Property) -> Iterable[str]:
        """Get all values of a property, returning an empty list if the property
        does not exist. This has better performance characteristics than `get()`
        as it does not need to resolve the property name.

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :return: An iterable of values.
        """
        try:
            return self._properties[prop.name]
        except KeyError:
            return []

    def first(self, prop: P, quiet: bool = False) -> str | None:
        """Get only the first value set for the property.

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :param quiet: a reference to an non-existent property will return
            an empty list instead of raising an error.
        :return: A value, or ``None``.
        """
        for value in self.get(prop, quiet=quiet):
            return value
        return None

    def has(self, prop: P, quiet: bool = False) -> bool:
        """Check to see if the given property has at least one value set.

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :param quiet: a reference to an non-existent property will return
            an empty list instead of raising an error.
        :return: a boolean.
        """
        prop_name = self._prop_name(prop, quiet=quiet)
        return prop_name in self._properties

    def add(
        self,
        prop: P,
        values: Values,
        cleaned: bool = False,
        quiet: bool = False,
        fuzzy: bool = False,
        format: str | None = None,
    ) -> None:
        """Add the given value(s) to the property if they are valid for
        the type of the property.

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :param values: either a single value, or a list of values to be added.
        :param cleaned: should the data be normalised before adding it.
        :param quiet: a reference to an non-existent property will return
            an empty list instead of raising an error.
        :param fuzzy: when normalising the data, should fuzzy matching be allowed.
        :param format: when normalising the data, formatting for a date.
        """
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None:
            return
        prop = self.schema.properties[prop_name]

        # Don't allow setting the reverse properties:
        if prop.stub:
            if quiet:
                return
            msg = gettext("Stub property (%s): %s")
            raise InvalidData(msg % (self.schema, prop))

        value: str | None = None
        for value in string_list(values, sanitize=not cleaned):
            self.unsafe_add(prop, value, cleaned=cleaned, fuzzy=fuzzy, format=format)
        return

    def unsafe_add(
        self,
        prop: Property,
        value: str | None,
        cleaned: bool = False,
        fuzzy: bool = False,
        format: str | None = None,
    ) -> str | None:
        """A version of `add()` to be used only in type-checking code. This accepts
        only a single value, and performs input cleaning on the premise that the
        value is already valid unicode. Returns the value that has been added."""
        if not cleaned and value is not None:
            format = format or prop.format
            value = prop.type.clean_text(value, fuzzy=fuzzy, format=format, proxy=self)

        if value is None:
            return None

        # Somewhat hacky: limit the maximum size of any particular
        # field to avoid overloading upstream aleph/elasticsearch.
        value_size = len(value)
        if prop.type.total_size is not None:
            if self._size + value_size > prop.type.total_size:
                # msg = "[%s] too large. Rejecting additional values."
                # log.warning(msg, prop.name)
                return None
        self._size += value_size
        self._properties.setdefault(prop.name, [])

        if value not in self._properties[prop.name]:
            self._properties[prop.name].append(value)

        return value

    def set(
        self,
        prop: P,
        values: Values,
        cleaned: bool = False,
        quiet: bool = False,
        fuzzy: bool = False,
        format: str | None = None,
    ) -> None:
        """Replace the values of the property with the given value(s).

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :param values: either a single value, or a list of values to be added.
        :param cleaned: should the data be normalised before adding it.
        :param quiet: a reference to an non-existent property will return
            an empty list instead of raising an error.
        """
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None:
            return
        self._properties.pop(prop_name, None)
        return self.add(
            prop, values, cleaned=cleaned, quiet=quiet, fuzzy=fuzzy, format=format
        )

    def pop(self, prop: P, quiet: bool = True) -> list[str]:
        """Remove all the values from the given property and return them.

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :param quiet: a reference to an non-existent property will return
            an empty list instead of raising an error.
        :return: a list of values, possibly empty.
        """
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None or prop_name not in self._properties:
            return []
        return list(self._properties.pop(prop_name))

    def remove(self, prop: P, value: str, quiet: bool = True) -> None:
        """Remove a single value from the given property. If it is not there,
        no action takes place.

        :param prop: can be given as a name or an instance of
            :class:`~followthemoney.property.Property`.
        :param value: will not be cleaned before checking.
        :param quiet: a reference to an non-existent property will return
            an empty list instead of raising an error.
        """
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is not None and prop_name in self._properties:
            try:
                self._properties[prop_name].remove(value)
            except (KeyError, ValueError):
                pass

    def iterprops(self) -> list[Property]:
        """Iterate across all the properties for which a value is set in
        the proxy (but do not return their values)."""
        return [self.schema.properties[p] for p in self._properties]

    def itervalues(self) -> Generator[tuple[Property, str], None, None]:
        """Iterate across all values in the proxy one by one, each given as a
        tuple of the property and the value."""
        for name, values in self._properties.items():
            prop = self.schema.properties[name]
            for value in values:
                yield (prop, value)

    def edgepairs(self) -> Generator[tuple[str, str], None, None]:
        """Return all the possible pairs of values for the edge source and target if
        the schema allows for an edge representation of the entity."""
        if self.schema.source_prop is not None and self.schema.target_prop is not None:
            sources = self.get(self.schema.source_prop)
            targets = self.get(self.schema.target_prop)
            yield from product(sources, targets)

    def get_type_values(
        self, type_: PropertyType, matchable: bool = False
    ) -> list[str]:
        """All values of a particular type associated with a the entity. For
        example, this lets you return all countries linked to an entity, rather
        than manually checking each property to see if it contains countries.

        :param type_: The type object to be searched.
        :param matchable: Whether to return only property values marked as matchable.
        """
        combined = set()
        for prop_name, values in self._properties.items():
            prop = self.schema.properties[prop_name]
            if prop.type is not type_:
                continue
            if matchable and not prop.matchable:
                continue
            combined.update(values)
        return list(combined)

    @property
    def names(self) -> list[str]:
        """Get the set of all name-type values set of the entity."""
        return self.get_type_values(registry.name)

    @property
    def countries(self) -> list[str]:
        """Get the set of all country-type values set of the entity."""
        return self.get_type_values(registry.country, matchable=True)

    @property
    def temporal_start(self) -> tuple[Property, str] | None:
        """Get a date that can be used to represent the start of the entity in a
        timeline. If there are multiple possible dates, the earliest date is
        returned."""
        values = []

        for prop in self.schema.temporal_start_props:
            values += [(prop, value) for value in self.get(prop.name)]

        values.sort(key=lambda tuple: tuple[1])
        return next(iter(values), None)

    @property
    def temporal_end(self) -> tuple[Property, str] | None:
        """Get a date that can be used to represent the end of the entity in a timeline.
        If therer are multiple possible dates, the latest date is returned."""
        values = []

        for prop in self.schema.temporal_end_props:
            values += [(prop, value) for value in self.get(prop.name)]

        values.sort(reverse=True, key=lambda tuple: tuple[1])
        return next(iter(values), None)

    def get_type_inverted(self, matchable: bool = False) -> dict[str, list[str]]:
        """Return all the values of the entity arranged into a mapping with the
        group name of their property type. These groups include ``countries``,
        ``addresses``, ``emails``, etc."""
        data: dict[str, list[str]] = {}
        for group, type_ in registry.groups.items():
            values = self.get_type_values(type_, matchable=matchable)
            if len(values) > 0:
                data[group] = values
        return data

    @property
    def caption(self) -> str:
        """The user-facing label to be used for this entity. This checks a list
        of properties defined by the schema (caption) and returns the first
        available value. If no caption is available, return the schema label."""
        for prop_ in self.schema.caption:
            prop = self.schema.properties[prop_]
            values = self.get(prop)
            if prop.type == registry.name and len(values) > 1:
                name = pick_name(sorted(values))
                if name is not None:
                    return name
            else:
                for value in values:
                    return value
        return self.schema.label

    @property
    def country_hints(self) -> builtins.set[str]:
        """Some property types, such as phone numbers and IBAN codes imply a
        country that may be associated with the entity. This list can be used
        for a more generous matching approach than the actual country values."""
        countries = set(self.countries)
        if len(countries) == 0:
            for prop, value in self.itervalues():
                if not prop.matchable:
                    continue
                hint = prop.type.country_hint(value)
                if hint is not None:
                    countries.add(hint)
        return countries

    @property
    def properties(self) -> dict[str, list[str]]:
        """Return a mapping of the properties and set values of the entity."""
        return {p: list(vs) for p, vs in self._properties.items()}

    def to_dict(self) -> dict[str, Any]:
        """Serialise the proxy into a dictionary with the defined properties, ID,
        schema and any contextual values that were handed in initially. The resulting
        dictionary can be used to make a new proxy, and it is commonly written to disk
        or a database."""
        data: dict[str, Any] = dict(self.context)
        data["id"] = self.id
        data["schema"] = self.schema.name
        data["properties"] = self.properties
        return data

    def to_statement_dict(self) -> dict[str, Any]:
        """Serialise the entity with its statements embedded, preserving the
        dataset (and other) provenance of each individual value.

        Only :class:`~followthemoney.statement.StatementEntity` tracks
        statements; a plain proxy carries provenance at the entity level only
        and cannot reconstruct it per value, so it has nothing faithful to emit."""
        raise NotImplementedError("Statement serialisation requires a StatementEntity.")

    def to_full_dict(self, matchable: bool = False) -> dict[str, Any]:
        """Return a serialised version of the entity with inverted type groups mixed
        in. See :meth:`~get_type_inverted`."""
        data = self.to_dict()
        data.update(self.get_type_inverted(matchable=matchable))
        return data

    def clone(self) -> Self:
        """Make a deep copy of the current entity proxy."""
        return self.__class__.from_dict(self.to_dict())

    def merge(self, other: "EntityProxy") -> Self:
        """Merge another entity proxy into this one. This will try and find
        the common schema between both entities and then add all property
        values from the other entity into this one."""
        model = self.schema.model
        self.id = self.id or other.id
        try:
            self.schema = model.common_schema(self.schema, other.schema)
        except InvalidData as e:
            raise InvalidData(f"Cannot merge entities with id {self.id}: {e}")

        self.context = merge_context(self.context, other.context)
        for prop, values in other._properties.items():
            self.add(prop, values, cleaned=True, quiet=True)
        return self

    def _checksum_digest(self) -> "_Hash":
        """Create a SHA1 digest of the entity's ID, schema and properties for
        change detection. This is returned as a hashlib digest object so that
        it can be subclassed."""
        digest = hashlib.sha1()
        if self.id is not None:
            digest.update(self.id.encode(HASH_ENCODING))
        digest.update(self.schema.name.encode(HASH_ENCODING))
        for prop in sorted(self._properties.keys()):
            digest.update(prop.encode(HASH_ENCODING))
            for value in sorted(self._properties[prop]):
                digest.update(value.encode(HASH_ENCODING))
                digest.update(b"\x1e")
            digest.update(b"\x1f")
        return digest

    @property
    def checksum(self) -> str:
        """A SHA1 checksum hexdigest representing the current state of the
        entity proxy. This can be used for change detection."""
        return self._checksum_digest().hexdigest()

    def __getstate__(self) -> dict[str, Any]:
        data = {slot: getattr(self, slot) for slot in self.__slots__}
        data["schema"] = self.schema.name
        return data

    def __setstate__(self, data: dict[str, Any]) -> None:
        for slot in self.__slots__:
            value = data.get(slot)
            if slot == "schema":
                value = Model.instance()[data["schema"]]
            setattr(self, slot, value)

    def __str__(self) -> str:
        return self.caption

    def __repr__(self) -> str:
        return f"<E({self.id!r},{self.schema.name},{str(self)!r})>"

    def __len__(self) -> int:
        return self._size

    def __hash__(self) -> int:
        if self.id is None:
            raise RuntimeError("Unhashable entity proxy without ID.")
        return hash(self.id)

    def __eq__(self, other: Any) -> bool:
        try:
            if self.id is None or other.id is None:
                raise RuntimeError("Cannot compare entity proxies without IDs.")
            return bool(self.id == other.id)
        except AttributeError:
            return False

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        cleaned: bool = True,
    ) -> Self:
        """Instantiate a proxy based on the given model and serialised dictionary.

        Use :meth:`followthemoney.model.Model.get_proxy` instead."""
        schema = Model.instance().get(data.get("schema", ""))
        if schema is None:
            raise InvalidData(gettext("No schema for entity."))
        return cls(schema, data, cleaned=cleaned)
