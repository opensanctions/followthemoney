import re
from typing import TYPE_CHECKING, Any, TypedDict

from banal import as_bool
from rigour.ids import get_identifier_format

from followthemoney.exc import InvalidData, InvalidModel
from followthemoney.types import registry
from followthemoney.util import const, gettext

if TYPE_CHECKING:
    from followthemoney.model import Model
    from followthemoney.schema import Schema

# Invalid property names.
RESERVED = ["id", "caption", "schema", "schemata", "referents", "datasets"]
PROP_NAME_RE = re.compile("^[a-z][a-zA-Z0-9]*$")


def check_property_name(name: str) -> bool:
    if name in RESERVED:
        return False
    if not PROP_NAME_RE.match(name):
        return False
    return True


class ReverseSpec(TypedDict, total=False):
    name: str
    label: str | None
    hidden: bool | None


class PropertyDict(TypedDict, total=False):
    label: str | None
    description: str | None
    type: str | None
    hidden: bool | None
    matchable: bool | None
    deprecated: bool | None
    maxLength: int | None
    examples: list[str] | None
    # stub: Optional[bool]
    range: str | None
    format: str | None


class PropertySpec(PropertyDict):
    reverse: ReverseSpec


class PropertyToDict(PropertyDict, total=False):
    name: str
    qname: str
    reverse: str | None
    stub: bool | None


class Property:
    """A definition of a value-holding field on a schema. Properties define
    the field type and other possible constraints. They also serve as entity
    to entity references."""

    __slots__ = (
        "_description",
        "_hash",
        "_label",
        "_range",
        "_reverse",
        "deprecated",
        "examples",
        "format",
        "hidden",
        "matchable",
        "max_length",
        "model",
        "name",
        "qname",
        "range",
        "reverse",
        "schema",
        "stub",
        "type",
    )

    def __init__(self, schema: "Schema", name: str, data: PropertySpec) -> None:
        #: The schema which the property is defined for. This is always the
        #: most abstract schema that has this property, not the possible
        #: child schemata that inherit it.
        self.schema = schema

        #: Machine-readable name for this property.
        self.name = name
        if not check_property_name(self.name):
            raise InvalidModel(f"Invalid name: {self.name}")

        #: Qualified property name, which also includes the schema name.
        self.qname = const(f"{schema.name}:{self.name}")

        self._label = data.get("label", name)
        self._description = data.get("description")
        self._hash = hash(f"<Property({self.qname!r})>")

        #: This property is deprecated and should not be used.
        self.deprecated = as_bool(data.get("deprecated", False))

        #: This property should not be shown or mentioned in the user interface.
        self.hidden = as_bool(data.get("hidden"))

        type_ = data.get("type") or "string"
        #: The data type for this property.
        self.type = registry.get(type_)
        if self.type is None:
            raise InvalidModel(f"Invalid type: {type_}")

        #: Whether this property should be used for matching and cross-referencing.
        _matchable = data.get("matchable")
        if _matchable is not None:
            self.matchable = as_bool(data.get("matchable"))
        else:
            self.matchable = self.type.matchable

        #: The maximum length of the property value.
        self.max_length = int(data.get("maxLength") or self.type.max_length)

        #: If the property is of type ``entity``, the set of valid schema to be added
        #: in this property can be constrained. For example, an asset can be owned,
        #: but a person cannot be owned.
        self._range = data.get("range")
        self.range: Schema | None = None

        #: If the property is of type ``identifier``, a more narrow definition of the
        #: identifier format can be provided. For example, LEI, INN or IBAN codes
        #: can be automatically validated.
        self.format: str | None = data.get("format")

        #: When a property points to another schema, a reverse property is added for
        #: various administrative reasons. These properties are, however, not real
        #: and cannot be written to. That's why they are marked as stubs and adding
        #: values to them will raise an exception.
        self.stub: bool | None = False

        #: When a property points to another schema, a stub reverse property is
        #: added as a place to store metadata to help display the link in inverted
        #: views. This is optional: a property may deliberately omit its ``reverse``
        #: when the inverse is an unbounded one-to-many fan-out that should not be
        #: materialised (a hub entity referenced by thousands of others). Without a
        #: reverse, the link is not surfaced by inverted lookups (``get_inverted``).
        self._reverse = data.get("reverse")
        self.reverse: Property | None = None

        #: Example values for this property, which can be used in the user interface to
        #: illustrate the expected format of the value.
        examples = data.get("examples")
        if examples is not None:
            examples = [str(e) for e in examples if e is not None]
            examples = examples if len(examples) > 0 else None
        self.examples: list[str] | None = examples

    def generate(self, model: "Model") -> None:
        """Setup method used when loading the model in order to build out the reverse
        links of the property."""
        model.properties.add(self)

        if self.type == registry.entity:
            if self.range is None and self._range is not None:
                self.range = model.get(self._range)

            if self.reverse is None and self.range and self._reverse:
                if not isinstance(self._reverse, dict):
                    raise InvalidModel(f"Invalid reverse: {self}")
                self.reverse = self.range._add_reverse(model, self._reverse, self)

        if self.type == registry.identifier and self.format is not None:
            format_ = get_identifier_format(self.format)
            if format_ is None or format_.NAME != self.format:
                raise InvalidModel(f"Invalid identifier format: {self.format}")
            # Internalize the string:
            self.format = format_.NAME

    @property
    def label(self) -> str:
        """User-facing title for this property."""
        return gettext(self._label)

    @property
    def description(self) -> str:
        """A longer description of the semantics of this property."""
        return gettext(self._description)

    def specificity(self, value: str) -> float:
        """Return a measure of how precise the given value is."""
        if not self.matchable:
            return 0.0
        return self.type.specificity(value)

    def caption(self, value: str) -> str:
        """Return a user-friendly caption for the given value."""
        return self.type.caption(value, format=self.format)

    def validate(self, data: list[str]) -> str | None:
        """Validate that the data should be stored.

        Since the types system doesn't really have validation, this currently
        tries to normalize the value to see if it passes strict parsing.
        """
        if self.stub:
            return gettext("Property cannot be written")
        for val in data:
            if not self.type.validate(val):
                err = gettext("Invalid value:")
                return f"{err} {val!r}"
        return None

    def __eq__(self, other: Any) -> bool:
        return self._hash == hash(other)

    def __hash__(self) -> int:
        return self._hash

    def to_dict(self) -> PropertyToDict:
        """Return property metadata in a serializable form."""
        data: PropertyToDict = {
            "name": self.name,
            "qname": self.qname,
            "label": self.label,
            "type": self.type.name,
            "maxLength": self.max_length,
        }
        if self.description:
            data["description"] = self.description
        if self.stub:
            data["stub"] = True
        if self.matchable:
            data["matchable"] = True
        if self.hidden:
            data["hidden"] = True
        if self.deprecated:
            data["deprecated"] = True
        if self.range is not None:
            data["range"] = self.range.name
        if self.reverse is not None:
            data["reverse"] = self.reverse.name
        if self.format is not None:
            data["format"] = self.format
        if self.examples is not None:
            data["examples"] = self.examples
        return data

    def __reduce__(self) -> Any:
        return (self._reconstruct, (self.qname,))

    @classmethod
    def _reconstruct(cls, qname: str) -> "Property":
        from followthemoney.model import Model

        prop = Model.instance().get_qname(qname)
        if prop is None:
            raise InvalidData(f"Unknown property: {qname!r}")
        return prop

    def __repr__(self) -> str:
        return f"<Property({self.qname!r})>"

    def __str__(self) -> str:
        return self.qname
