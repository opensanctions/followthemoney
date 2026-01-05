import hashlib
import warnings
from sqlalchemy.engine import Row
from typing import Union, cast
from typing import Any, Dict, Generator, Optional, TypeGuard
from typing_extensions import TypedDict, Self
from rigour.time import datetime_iso, iso_datetime
from rigour.boolean import bool_text

from followthemoney.proxy import EntityProxy
from followthemoney.statement.util import get_prop_type, BASE_ID, NON_LANG_TYPE_NAMES
from followthemoney.util import HASH_ENCODING


UNSET = object()


def is_not_unset(value: str | None | object) -> TypeGuard[str | None]:
    return value is not UNSET


class StatementDict(TypedDict):
    id: Optional[str]
    entity_id: str
    canonical_id: str
    prop: str
    schema: str
    value: str
    dataset: str
    lang: Optional[str]
    original_value: Optional[str]
    external: bool
    first_seen: Optional[str]
    last_seen: Optional[str]
    origin: Optional[str]


class Statement(object):
    """A single statement about a property relevant to an entity.

    For example, this could be used to say: "In dataset A, entity X has the
    property `name` set to 'John Smith'. I first observed this at K, and last
    saw it at L."

    Null property values are not supported. This might need to change if we
    want to support making property-less entities.
    """

    BASE = BASE_ID

    __slots__ = [
        "id",
        "_entity_id",
        "canonical_id",
        "_prop",
        "_schema",
        "_value",
        "_dataset",
        "_lang",
        "prop_type",
        "original_value",
        "_external",
        "first_seen",
        "last_seen",
        "origin",
    ]

    def __init__(
        self,
        entity_id: str,
        prop: str,
        schema: str,
        value: str,
        dataset: str,
        lang: Optional[str] = None,
        original_value: Optional[str] = None,
        first_seen: Optional[str] = None,
        external: bool = False,
        id: Optional[str] = None,
        canonical_id: Optional[str] = None,
        last_seen: Optional[str] = None,
        origin: Optional[str] = None,
    ):
        self._entity_id = entity_id
        self.canonical_id = canonical_id or entity_id
        self._prop = prop
        self._schema = schema
        self.prop_type = get_prop_type(schema, prop)
        self._value = value
        self._dataset = dataset

        # Remove lang for non-linguistic property types. The goal here is to avoid
        # duplicate statements because of language tags, but the language metadata
        # may be relevant as context for how the original_value was parsed so it's
        # a bit of information loss.
        if lang is not None:
            if self.prop_type in NON_LANG_TYPE_NAMES:
                lang = None
        self._lang = lang

        self.original_value = original_value
        self.first_seen = first_seen
        self.last_seen = last_seen or first_seen
        self._external = external
        self.origin = origin
        if id is None:
            id = self.generate_key()
        self.id = id

    @property
    def entity_id(self) -> str:
        """The (original) ID of the entity this statement is about."""
        return self._entity_id

    @property
    def dataset(self) -> str:
        """The dataset this statement was observed in."""
        return self._dataset

    @property
    def prop(self) -> str:
        """The property name this statement is about."""
        return self._prop

    @property
    def schema(self) -> str:
        """The schema of the entity this statement is about."""
        return self._schema

    @property
    def value(self) -> str:
        """The value of the property captured by this statement."""
        return self._value

    @property
    def lang(self) -> Optional[str]:
        """The language of the property value, if applicable."""
        return self._lang

    @property
    def external(self) -> bool:
        """Whether this statement was observed in an external dataset."""
        return self._external

    def to_dict(self) -> StatementDict:
        return {
            "canonical_id": self.canonical_id,
            "entity_id": self._entity_id,
            "prop": self._prop,
            "schema": self._schema,
            "value": self._value,
            "dataset": self._dataset,
            "lang": self._lang,
            "original_value": self.original_value,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "external": self._external,
            "origin": self.origin,
            "id": self.id,
        }

    def to_csv_row(self) -> Dict[str, Optional[str]]:
        data = cast(Dict[str, Optional[str]], self.to_dict())
        data["external"] = bool_text(self._external)
        data["prop_type"] = self.prop_type
        return data

    def to_db_row(self) -> Dict[str, Any]:
        data = cast(Dict[str, Any], self.to_dict())
        data["first_seen"] = iso_datetime(self.first_seen)
        data["last_seen"] = iso_datetime(self.last_seen)
        data["prop_type"] = self.prop_type
        return data

    def __hash__(self) -> int:
        if self.id is None:
            warnings.warn(
                "Hashing a statement without an ID results in undefined behaviour",
                RuntimeWarning,
            )
        return hash(self.id)

    def __repr__(self) -> str:
        return "<Statement(%r, %r, %r)>" % (self._entity_id, self._prop, self._value)

    def __eq__(self, other: Any) -> bool:
        return not self.id != other.id

    def __lt__(self, other: Any) -> bool:
        self_key = (self._prop != BASE_ID, self.id or "")
        other_key = (other._prop != BASE_ID, other.id or "")
        return self_key < other_key

    def clone(
        self: Self,
        *,
        entity_id: Optional[str] = None,
        prop: Optional[str] = None,
        schema: Optional[str] = None,
        value: Optional[str] = None,
        dataset: Optional[str] = None,
        lang: Union[str, None, object] = UNSET,
        original_value: Union[str, None, object] = UNSET,
        first_seen: Union[str, None, object] = UNSET,
        external: Optional[bool] = None,
        canonical_id: Optional[str] = None,
        last_seen: Union[str, None, object] = UNSET,
        origin: Union[str, None, object] = UNSET,
    ) -> "Statement":
        """Make a deep copy of the given statement."""
        lang = lang if is_not_unset(lang) else self._lang
        ov = original_value if is_not_unset(original_value) else self.original_value
        first_seen = first_seen if is_not_unset(first_seen) else self.first_seen
        last_seen = last_seen if is_not_unset(last_seen) else self.last_seen
        origin = origin if is_not_unset(origin) else self.origin
        if external is None:
            external = self._external
        if canonical_id is None and self._entity_id != self.canonical_id:
            canonical_id = self.canonical_id

        # Decide if the statement ID can be kept the same:
        stmt_id = self.id
        if entity_id is not None and entity_id != self.entity_id:
            stmt_id = None
        if prop is not None and prop != self._prop:
            stmt_id = None
        if schema is not None and schema != self._schema:
            stmt_id = None
        if value is not None and value != self._value:
            stmt_id = None
        if dataset is not None and dataset != self._dataset:
            stmt_id = None
        if external != self._external:
            stmt_id = None
        if lang != self._lang:
            stmt_id = None
        return Statement(
            id=stmt_id,
            entity_id=entity_id or self._entity_id,
            prop=prop or self._prop,
            schema=schema or self._schema,
            value=value or self._value,
            dataset=dataset or self._dataset,
            lang=lang,
            original_value=ov,
            first_seen=first_seen,
            external=external,
            canonical_id=canonical_id,
            last_seen=last_seen,
            origin=origin,
        )

    def generate_key(self) -> Optional[str]:
        return self.make_key(
            self._dataset,
            self._entity_id,
            self._prop,
            self._value,
            self._external,
            lang=self._lang,
        )

    @classmethod
    def make_key(
        cls,
        dataset: str,
        entity_id: str,
        prop: str,
        value: str,
        external: Optional[bool],
        lang: Optional[str] = None,
    ) -> Optional[str]:
        """Hash the key properties of a statement record to make a unique ID."""
        if prop is None or value is None:
            return None
        if lang is None:
            key = f"{dataset}.{entity_id}.{prop}.{value}"
        else:
            key = f"{dataset}.{entity_id}.{prop}.{value}@{lang}"
        if external:
            # We consider the external flag in key composition to avoid race conditions
            # where a certain entity might be emitted as external while it is already
            # linked in to the graph via another route.
            key = f"{key}.ext"
        return hashlib.sha1(key.encode(HASH_ENCODING)).hexdigest()

    @classmethod
    def from_dict(cls, data: StatementDict) -> "Statement":
        return cls(
            entity_id=data["entity_id"],
            prop=data["prop"],
            schema=data["schema"],
            value=data["value"],
            dataset=data["dataset"],
            lang=data.get("lang", None),
            original_value=data.get("original_value", None),
            first_seen=data.get("first_seen", None),
            external=data.get("external", False),
            id=data.get("id", None),
            canonical_id=data.get("canonical_id", None),
            last_seen=data.get("last_seen", None),
            origin=data.get("origin", None),
        )

    @classmethod
    def from_db_row(cls, row: Row[Any]) -> "Statement":
        return cls(
            id=row.id,
            canonical_id=row.canonical_id,
            entity_id=row.entity_id,
            prop=row.prop,
            schema=row.schema,
            value=row.value,
            dataset=row.dataset,
            lang=row.lang,
            original_value=row.original_value,
            first_seen=datetime_iso(row.first_seen),
            external=row.external,
            last_seen=datetime_iso(row.last_seen),
            origin=row.origin,
        )

    @classmethod
    def from_entity(
        cls,
        entity: "EntityProxy",
        dataset: str,
        first_seen: Optional[str] = None,
        last_seen: Optional[str] = None,
        external: bool = False,
        origin: Optional[str] = None,
    ) -> Generator["Statement", None, None]:
        from followthemoney.statement.entity import StatementEntity

        if entity.id is None:
            raise ValueError("Cannot create statements for entity without ID!")

        # If the entity is already a StatementEntity, we return its statements directly.
        if isinstance(entity, StatementEntity):
            yield from entity.statements
            return

        yield cls(
            entity_id=entity.id,
            prop=BASE_ID,
            schema=entity.schema.name,
            value=entity.id,
            dataset=dataset,
            external=external,
            first_seen=first_seen,
            last_seen=last_seen,
            origin=origin,
        )
        for prop, value in entity.itervalues():
            yield cls(
                entity_id=entity.id,
                prop=prop.name,
                schema=entity.schema.name,
                value=value,
                dataset=dataset,
                external=external,
                first_seen=first_seen,
                last_seen=last_seen,
                origin=origin,
            )
