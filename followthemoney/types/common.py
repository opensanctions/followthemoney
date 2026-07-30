from collections.abc import Callable, Sequence
from inspect import cleandoc
from itertools import product
from typing import TYPE_CHECKING, Any, TypedDict

from babel.core import Locale
from normality import stringify

from followthemoney.util import const, get_locale, gettext, sanitize_text
from followthemoney.value import Value

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy

EnumValues = dict[str, str]


class PropertyTypeToDict(TypedDict, total=False):
    label: str
    plural: str
    description: str | None
    maxLength: int
    group: str | None
    matchable: bool | None
    pivot: bool | None
    values: EnumValues | None


class PropertyType:
    """Base class for all FtM property types.

    Every property defined on a schema has a `type` attribute that points to a
    `PropertyType` instance. The type is responsible for cleaning incoming values,
    validating them, comparing them against other values of the same type, and
    producing display labels and graph node IDs.

    Concrete types (`NameType`, `DateType`, `CountryType`, etc.) are instantiated
    once at module load and exposed as singletons on the `registry`. Application
    code should access them by name — `registry.name`, `registry.date`,
    `registry.country` — rather than instantiating them directly."""

    name: str = const("any")
    """A machine-facing, variable safe name for the given type."""

    group: str | None = None
    """Groups are used to invert all the properties of an entity that have a
    given  type into a single list before indexing them. This way, in Aleph,
    you can query for ``countries:gb`` instead of having to make a set of filters
    like ``properties.jurisdiction:gb OR properties.country:gb OR ...``."""

    label: str = "Any"
    """A name for this type to be shown to users."""

    plural: str = "Any"
    """A plural name for this type which can be used in appropriate places in
    a user interface."""

    matchable: bool = True
    """Matchable types allow properties to be compared with each other in order to
    assess entity similarity. While it makes sense to compare names, countries or
    phone numbers, the same isn't true for raw JSON blobs or descriptive text
    snippets."""

    pivot: bool = False
    """Pivot property types are like a stronger form of :attr:`~matchable` types:
    they will be used when value-based lookups are used to find commonalities
    between entities. For example, pivot typed-properties are used to show all the
    other entities that mention the same phone number, email address or name as the
    one currently seen by the user."""

    max_length: int = 250
    """The maximum length of a single value of this type. This is used to warn when
    adding individual values that may be malformed or too long to be stored in
    downstream databases with fixed column lengths. The unit is unicode codepoints
    (not bytes), the output of Python len()."""

    total_size: int | None = None
    """Some types have overall size limitations in place in order to avoid generating
    entities that are very large (upstream ElasticSearch has a 100MB document limit).
    Once the total size of all properties of this type has exceed the given limit,
    an entity will refuse to add further values."""

    @property
    def docs(self) -> str | None:
        if not self.__doc__:
            return None

        return cleandoc(self.__doc__)

    def validate(
        self, value: str, fuzzy: bool = False, format: str | None = None
    ) -> bool:
        """Returns a boolean to indicate if the given value is a valid instance of
        the type."""
        cleaned = self.clean_text(value, fuzzy=fuzzy, format=format)
        if cleaned is None or len(cleaned) == 0:
            return False
        return len(cleaned) <= self.max_length

    def clean(
        self,
        raw: Value,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        """Convert a raw value into its canonical form for storage on an entity.

        Returns `None` if the value is empty or cannot be interpreted as this type.
        The `fuzzy` flag loosens validation for types that support it (dates,
        identifiers). `format` supplies a type-specific hint — a `strptime` format
        string for dates, or the country a phone number is dialed in. `proxy` is
        the entity the value is being added to, which a few types use for
        context-aware cleaning (an entity reference cannot point at itself, for
        example).

        This method converts the input to a string, drops null-equivalents, and
        then delegates to `clean_text`. Subclasses normally override `clean_text`
        rather than this method."""
        text = sanitize_text(raw)
        if text is None:
            return None
        return self.clean_text(text, fuzzy=fuzzy, format=format, proxy=proxy)

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        """Type-specific cleaning hook.

        Override this in subclasses to normalize a non-null string value into the
        type's canonical representation. Return `None` to reject the value. The
        base implementation is a pass-through. `clean()` calls this after
        stringifying the input and filtering nulls."""
        return text

    def join(self, values: Sequence[str]) -> str:
        """Render multiple values of this type as a single string.

        Used when flattening multi-valued properties into formats that allow only
        one value per cell (CSV, some RDF serializations). Values are joined with
        `; `. The transformation is not reversible — use only at the final
        serialization step."""
        return "; ".join(values)

    def _specificity(self, value: str) -> float:
        return 1.0

    def specificity(self, value: str | None) -> float:
        """Return a score for how specific the given value is. This can be used as a
        weighting factor in entity comparisons in order to rate matching property
        values by how specific they are. For example: a longer address is considered
        to be more specific than a short one, a full date more specific than just a
        year number, etc."""
        if not self.matchable or value is None:
            return 0.0
        return self._specificity(value)

    def compare_safe(self, left: str | None, right: str | None) -> float:
        """Variant of `compare()` that accepts `None` on either side.

        Returns `0.0` if either argument is missing. Otherwise delegates to
        `compare()`."""
        left = stringify(left)
        right = stringify(right)
        if left is None or right is None:
            return 0.0
        return self.compare(left, right)

    def compare(self, left: str, right: str) -> float:
        """Score the similarity of two values of this type.

        Returns a float in `[0.0, 1.0]`: `0.0` means the values carry no evidence
        of matching, `1.0` means they are identical in the strongest
        type-specific sense. Intermediate values quantify partial similarity —
        for names, the Levenshtein ratio; for countries, territory overlap; for
        dates, precision-aware proximity.

        The base implementation does a lowercase equality check weighted by
        `specificity()`, so a match on a longer, more specific value scores higher
        than a match on a short one. Subclasses override this for richer
        comparisons.

        Values are assumed to be cleaned (output of `clean()`) but not further
        normalized — `compare` is the right place to apply type-specific
        normalization before matching."""
        if left.lower() == right.lower():
            return 1.0 * self.specificity(left)
        return 0.0

    def compare_sets(
        self,
        left: Sequence[str],
        right: Sequence[str],
        func: Callable[[Sequence[float]], float] = max,
    ) -> float:
        """Score the similarity of two value sets by reducing pairwise comparisons.

        Every element of `left` is compared to every element of `right`, and the
        resulting scores are reduced with `func` — `max` by default, so the best
        pairwise match wins. Returns `0.0` if either set is empty. Pass `func=sum`
        or a statistical mean for alternative aggregation strategies."""
        results = []
        for le, ri in product(left, right):
            results.append(self.compare(le, ri))
        if len(results) == 0:
            return 0.0
        return func(results)

    def country_hint(self, value: str) -> str | None:
        """Determine if the given value allows us to infer a country that it may
        be related to (e.g. using a country prefix on a phone number or IBAN)."""
        return None

    def pick(self, values: Sequence[str]) -> str | None:
        """Choose the best representative value from a set of alternatives.

        Used when a UI needs to display a single value for a multi-valued
        property, or when reducing a set of similar values to a canonical form
        (for example, picking the most complete variant of a name). Subclasses
        that support picking — notably `NameType` — implement type-specific
        heuristics. The base implementation raises `NotImplementedError`."""
        raise NotImplementedError

    def node_id(self, value: str) -> str | None:
        """Build a graph node ID for a typed property value.

        Used by graph exporters (Cypher, GEXF, Neo4J bulk) when [reifying](
        ../docs/cli.md#graph-exports-cypher-gexf-neo4j-bulk) property values
        into their own graph nodes — for example, turning every phone number
        mentioned by any entity into a single node connected to the entities
        that carry it. The default encoding is `{type}:{value}`, matching the
        RDF URN form."""
        return f"{self.name}:{value}"

    def node_id_safe(self, value: str | None) -> str | None:
        """Wrapper for node_id to handle None values."""
        if value is None:
            return None
        return self.node_id(value)

    def caption(self, value: str, format: str | None = None) -> str:
        """Return a label for the given property value. This is often the same as the
        value, but for types like countries or languages, it would return the label,
        while other values like phone numbers can be formatted to be nicer to read."""
        return value

    def to_dict(self) -> PropertyTypeToDict:
        """Return a serialisable description of this data type."""
        data: PropertyTypeToDict = {
            "label": gettext(self.label),
            "plural": gettext(self.plural),
            "description": gettext(self.docs),
            "maxLength": self.max_length,
        }
        if self.group:
            data["group"] = self.group
        if self.matchable:
            data["matchable"] = True
        if self.pivot:
            data["pivot"] = True
        return data

    def __eq__(self, other: Any) -> bool:
        try:
            return self.name == other.name  # type: ignore
        except AttributeError:
            return False

    def __hash__(self) -> int:
        return hash(self.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<{self.name}>"


class EnumType(PropertyType):
    """Enumerated type properties are used for types which have a defined set
    of possible values, like languages and countries."""

    def __init__(self) -> None:
        self._names: dict[Locale, EnumValues] = {}
        self.codes = set(self.names.keys())

    def _locale_names(self, locale: Locale) -> EnumValues:
        return {}

    @property
    def names(self) -> EnumValues:
        """Return a mapping from property values to their labels in the current
        locale."""
        locale = get_locale()
        if locale not in self._names:
            self._names[locale] = self._locale_names(locale)
        return self._names[locale]

    def validate(
        self, value: str, fuzzy: bool = False, format: str | None = None
    ) -> bool:
        """Make sure that the given code value is one of the supported set."""
        return str(value).lower().strip() in self.codes

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        """All code values are cleaned to be lowercase and trailing whitespace is
        removed."""
        code = text.lower().strip()
        if code not in self.codes:
            return None
        return code

    def caption(self, value: str, format: str | None = None) -> str:
        """Given a code value, return the label that should be shown to a user."""
        return self.names.get(value, value)

    def to_dict(self) -> PropertyTypeToDict:
        """When serialising the model to JSON, include all values."""
        data = super().to_dict()
        data["values"] = self.names
        return data
