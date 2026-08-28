from collections.abc import Generator, Iterable, Mapping
from hashlib import sha1
from typing import TYPE_CHECKING, Any, Self, TypeVar

from rigour.langs import LangStr
from rigour.names.pick import pick_lang_name

from followthemoney.dataset import Dataset, UndefinedDataset
from followthemoney.exc import InvalidData
from followthemoney.model import Model
from followthemoney.property import Property
from followthemoney.proxy import EntityProxy, P
from followthemoney.schema import Schema
from followthemoney.statement.statement import Statement
from followthemoney.statement.util import BASE_ID
from followthemoney.types import registry
from followthemoney.types.common import PropertyType
from followthemoney.util import HASH_ENCODING, gettext
from followthemoney.value import Values, string_list

SE = TypeVar("SE", bound="StatementEntity")

if TYPE_CHECKING:
    from hashlib import _Hash


class StatementEntity(EntityProxy):
    """An entity object that can link to a set of datasets that it is sourced from."""

    __slots__ = (
        "_caption",
        "_statements",
        "dataset",
        "extra_referents",
        "id",
        "last_change",
        "schema",
    )

    def __init__(
        self,
        dataset: Dataset,
        data: dict[str, Any],
        cleaned: bool = True,
    ) -> None:
        data = dict(data or {})
        schema = Model.instance().get(data.pop("schema", None))
        if schema is None:
            raise InvalidData(gettext("No schema for entity."))
        self.schema = schema

        self._caption: str | None = None
        """A pre-computed label for this entity."""

        self.extra_referents: set[str] = set(data.pop("referents", []))
        """The IDs of all entities which are included in this canonical entity."""

        self.last_change: str | None = data.get("last_change", None)
        """The last time this entity was changed."""

        self.dataset = dataset
        """The default dataset for new statements."""

        self.id: str | None = data.pop("id", None)
        self._statements: dict[str, set[Statement]] = {}

        properties = data.pop("properties", None)
        if isinstance(properties, Mapping):
            for key, value in properties.items():
                self.add(key, value, cleaned=cleaned, quiet=True)

        for stmt_data in data.pop("statements", []):
            stmt = Statement.from_dict(stmt_data)
            if self.id is not None:
                stmt.canonical_id = self.id
            self.add_statement(stmt)

    @property
    def _properties(self) -> dict[str, list[str]]:  # type: ignore
        return {p: [s.value for s in v] for p, v in self._statements.items()}

    def _iter_stmt(self) -> Generator[Statement, None, None]:
        for stmts in self._statements.values():
            for stmt in stmts:
                if stmt.entity_id is None and self.id is not None:
                    stmt = stmt.clone(entity_id=self.id)
                if stmt.id is None:
                    stmt.id = stmt.generate_key()
                yield stmt

    @property
    def statements(self) -> Generator[Statement, None, None]:
        """Return all statements for this entity, with extra ID statement."""
        ids: list[str] = []
        last_seen: set[str] = set()
        first_seen: set[str] = set()
        for stmt in self._iter_stmt():
            yield stmt
            if stmt.id is not None:
                ids.append(stmt.id)
            if stmt.last_seen is not None:
                last_seen.add(stmt.last_seen)
            if stmt.first_seen is not None:
                first_seen.add(stmt.first_seen)
        if self.id is not None:
            digest = sha1(self.schema.name.encode(HASH_ENCODING))
            for id in sorted(ids):
                digest.update(id.encode(HASH_ENCODING))
            checksum = digest.hexdigest()
            # This is to make the last_change value stable across
            # serialisation:
            first = self.last_change or min(first_seen, default=None)
            yield Statement(
                canonical_id=self.id,
                entity_id=self.id,
                prop=BASE_ID,
                schema=self.schema.name,
                value=checksum,
                dataset=self.dataset.name,
                first_seen=first,
                last_seen=max(last_seen, default=None),
            )

    @property
    def first_seen(self) -> str | None:
        seen = (s.first_seen for s in self._iter_stmt() if s.first_seen is not None)
        return min(seen, default=None)

    @property
    def last_seen(self) -> str | None:
        seen = (s.last_seen for s in self._iter_stmt() if s.last_seen is not None)
        return max(seen, default=None)

    @property
    def external(self) -> bool:
        """Whether every statement backing this entity is external, i.e. the whole
        entity is a pre-verification suggestion rather than published data.

        Reach for this when deciding if an entity can be treated as real: a single
        non-external statement means some part of the entity has been verified, so
        the entity as a whole counts as internal. An entity without any statements
        is not external.
        """
        found = False
        for stmts in self._statements.values():
            for stmt in stmts:
                if not stmt.external:
                    return False
                found = True
        return found

    @property
    def datasets(self) -> set[str]:
        datasets: set[str] = set()
        for stmt in self._iter_stmt():
            datasets.add(stmt.dataset)
        return datasets

    @property
    def referents(self) -> set[str]:
        referents: set[str] = set(self.extra_referents)
        for stmt in self._iter_stmt():
            if stmt.entity_id is not None and stmt.entity_id != self.id:
                referents.add(stmt.entity_id)
        return referents

    @property
    def key_prefix(self) -> str | None:
        return self.dataset.name

    @key_prefix.setter
    def key_prefix(self, dataset: str | None) -> None:
        raise NotImplementedError()

    def add_statement(self, stmt: Statement) -> None:
        schema = self.schema
        if schema.name != stmt.schema and not schema.is_a(stmt.schema):
            try:
                self.schema = schema.model.common_schema(schema, stmt.schema)
            except InvalidData as exc:
                raise InvalidData(f"{self.id}: {exc}") from exc

        if stmt.prop == BASE_ID:
            if stmt.first_seen is not None:
                # The last_change attribute describes the latest checksum change
                # of any emitted component of the entity, which is stored in the BASE
                # field.
                if self.last_change is None:
                    self.last_change = stmt.first_seen
                else:
                    self.last_change = max(self.last_change, stmt.first_seen)
        else:
            self._caption = None
            if stmt.prop not in self._statements:
                self._statements[stmt.prop] = set()
            self._statements[stmt.prop].add(stmt)

    def get(self, prop: P, quiet: bool = False) -> list[str]:
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None or prop_name not in self._statements:
            return []
        return list({s.value for s in self._statements[prop_name]})

    def get_prop(self, prop: Property) -> Iterable[str]:
        try:
            statements = self._statements[prop.name]
            return {s.value for s in statements}
        except KeyError:
            return []

    def get_statements(self, prop: P, quiet: bool = False) -> list[Statement]:
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None or prop_name not in self._statements:
            return []
        return list(self._statements[prop_name])

    @property
    def has_statements(self) -> bool:
        """Return whether the entity has any statements."""
        return len(self._statements) > 0

    def set(
        self,
        prop: P,
        values: Values,
        cleaned: bool = False,
        quiet: bool = False,
        fuzzy: bool = False,
        format: str | None = None,
        lang: str | None = None,
        original_value: str | None = None,
        origin: str | None = None,
        external: bool = False,
    ) -> None:
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None:
            return
        self._statements.pop(prop_name, None)
        return self.add(
            prop,
            values,
            cleaned=cleaned,
            quiet=quiet,
            fuzzy=fuzzy,
            format=format,
            lang=lang,
            original_value=original_value,
            origin=origin,
            external=external,
        )

    def add(
        self,
        prop: P,
        values: Values,
        cleaned: bool = False,
        quiet: bool = False,
        fuzzy: bool = False,
        format: str | None = None,
        lang: str | None = None,
        original_value: str | None = None,
        origin: str | None = None,
        external: bool = False,
    ) -> None:
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None:
            return
        prop = self.schema.properties[prop_name]
        for value in string_list(values, sanitize=not cleaned):
            self.unsafe_add(
                prop,
                value,
                cleaned=cleaned,
                fuzzy=fuzzy,
                format=format,
                quiet=quiet,
                lang=lang,
                original_value=original_value,
                origin=origin,
                external=external,
            )
        return

    def unsafe_add(
        self,
        prop: Property,
        value: str | None,
        cleaned: bool = False,
        fuzzy: bool = False,
        format: str | None = None,
        quiet: bool = False,
        schema: str | None = None,
        dataset: str | None = None,
        seen: str | None = None,
        lang: str | None = None,
        original_value: str | None = None,
        origin: str | None = None,
        external: bool = False,
    ) -> str | None:
        """Add a statement to the entity, possibly the value."""
        if value is None or len(value) == 0:
            return None

        # Don't allow setting the reverse properties:
        if prop.stub:
            if quiet:
                return None
            msg = gettext("Stub property (%s): %s")
            raise InvalidData(msg % (self.schema, prop))

        if lang is not None:
            lang = registry.language.clean_text(lang)

        clean: str | None = value
        if not cleaned:
            clean = prop.type.clean_text(value, proxy=self, fuzzy=fuzzy, format=format)

        if clean is None:
            return None

        if not original_value:
            original_value = value

        if self.id is None:
            raise InvalidData("Cannot add statement to entity without ID!")
        stmt = Statement(
            entity_id=self.id,
            prop=prop.name,
            schema=schema or self.schema.name,
            value=clean,
            dataset=dataset or self.dataset.name,
            lang=lang,
            original_value=original_value,
            first_seen=seen,
            origin=origin,
            external=external,
        )
        self.add_statement(stmt)
        return clean

    def pop(self, prop: P, quiet: bool = True) -> list[str]:
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is None or prop_name not in self._statements:
            return []
        if prop_name in self.schema.caption:
            self._caption = None
        return list({s.value for s in self._statements.pop(prop_name, [])})

    def remove(self, prop: P, value: str, quiet: bool = True) -> None:
        prop_name = self._prop_name(prop, quiet=quiet)
        if prop_name is not None and prop_name in self._statements:
            stmts = {s for s in self._statements[prop_name] if s.value != value}
            self._statements[prop_name] = stmts
            if prop_name in self.schema.caption:
                self._caption = None

    def itervalues(self) -> Generator[tuple[Property, str], None, None]:
        for name, statements in self._statements.items():
            prop = self.schema.properties[name]
            for value in {s.value for s in statements}:
                yield (prop, value)

    def get_type_values(
        self, type_: PropertyType, matchable: bool = False
    ) -> list[str]:
        combined: set[str] = set()
        for stmt in self.get_type_statements(type_, matchable=matchable):
            combined.add(stmt.value)
        return list(combined)

    def get_type_statements(
        self, type_: PropertyType, matchable: bool = False
    ) -> list[Statement]:
        combined: list[Statement] = []
        for prop_name, statements in self._statements.items():
            prop = self.schema.properties[prop_name]
            # Used in performance-critical code paths:
            if prop.type is not type_:
                continue
            if matchable and not prop.matchable:
                continue
            combined.extend(statements)
        return combined

    @property
    def properties(self) -> dict[str, list[str]]:
        return {p: list({s.value for s in vs}) for p, vs in self._statements.items()}

    @property
    def caption(self) -> str:
        """The user-facing label to be used for this entity. This checks a list
        of properties defined by the schema (caption) and returns the first
        available value. If no caption is available, return the schema label.

        This implementation prefers statements where the language property is that
        of the preferred system language."""
        if self._caption is None:
            for prop_ in self.schema.caption:
                stmts = self._statements.get(prop_)
                if stmts is None:
                    continue
                prop = self.schema.properties[prop_]
                if prop.type == registry.name and len(stmts) > 1:
                    values = [LangStr(s.value, lang=s.lang) for s in stmts]
                    name = pick_lang_name(values)
                    if name is not None:
                        self._caption = name
                        return self._caption

                for stmt in sorted(stmts):
                    self._caption = stmt.value
                    return self._caption
            if self._caption is None:
                self._caption = self.schema.label
        return self._caption

    def iterprops(self) -> list[Property]:
        return [self.schema.properties[p] for p in self._statements]

    def clone(self) -> Self:
        data = {"schema": self.schema.name, "id": self.id}
        cloned = type(self)(self.dataset, data)
        for stmt in self._iter_stmt():
            cloned.add_statement(stmt)
        return cloned

    def merge(self, other: EntityProxy) -> Self:
        try:
            self.schema = self.schema.model.common_schema(self.schema, other.schema)
        except InvalidData as e:
            raise InvalidData(f"Cannot merge entities with id {self.id}: {e}")

        if not isinstance(other, StatementEntity):
            for prop, value in other.itervalues():
                self.unsafe_add(prop, value, cleaned=True, quiet=True)
            return self
        for stmt in other._iter_stmt():
            if self.id is not None:
                stmt.canonical_id = self.id
            self.add_statement(stmt)
        self.extra_referents.update(other.extra_referents)
        return self

    def to_context_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the entity for context."""
        data: dict[str, Any] = {
            "id": self.id,
            "caption": self.caption,
            "schema": self.schema.name,
        }
        referents: set[str | None] = set(self.extra_referents)
        datasets = set(self.datasets)
        origins: set[str] = set()
        first_seen = None
        last_seen = None
        for stmts in self._statements.values():
            for stmt in stmts:
                if stmt.first_seen is not None:
                    if first_seen is None or stmt.first_seen < first_seen:
                        first_seen = stmt.first_seen
                if stmt.last_seen is not None:
                    if last_seen is None or stmt.last_seen > last_seen:
                        last_seen = stmt.last_seen
                if stmt.entity_id is not None and stmt.entity_id != self.id:
                    referents.add(stmt.entity_id)
                datasets.add(stmt.dataset)
                if stmt.origin is not None:
                    origins.add(stmt.origin)

        data["referents"] = list(referents)
        data["datasets"] = [d for d in datasets if d != Dataset.UNDEFINED]
        if origins:
            data["origin"] = list(origins)

        if first_seen is not None:
            data["first_seen"] = first_seen
        if last_seen is not None:
            data["last_seen"] = last_seen
        if self.last_change is not None:
            data["last_change"] = self.last_change
        return data

    def to_dict(self) -> dict[str, Any]:
        data = self.to_context_dict()
        data["properties"] = self.properties
        return data

    def to_statement_dict(self) -> dict[str, Any]:
        """Return a dictionary representation of the entity's statements."""
        data = {
            "id": self.id,
            "caption": self.caption,
            "schema": self.schema.name,
            "statements": [stmt.to_dict() for stmt in self._iter_stmt()],
        }
        return data

    def _checksum_digest(self) -> "_Hash":
        """Create a SHA1 digest of the entity's ID, schema and properties for
        change detection. This is returned as a hashlib digest object so that
        it can be subclassed."""
        digest = sha1()
        if self.id is not None:
            digest.update(self.id.encode(HASH_ENCODING))
        statement_ids: list[str] = []
        for stmts in self._statements.values():
            for stmt in stmts:
                if stmt.id is not None:
                    statement_ids.append(stmt.id)
        for stmt_id in sorted(statement_ids):
            digest.update(stmt_id.encode(HASH_ENCODING))
            digest.update(b"\x1e")
        return digest

    def __len__(self) -> int:
        return len(list(self._iter_stmt())) + 1

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        cleaned: bool = True,
        default_dataset: Dataset | None = None,
    ) -> Self:
        # Exists only for backwards compatibility.
        dataset = default_dataset or UndefinedDataset
        return cls(dataset, data, cleaned=cleaned)

    @classmethod
    def from_data(
        cls,
        dataset: Dataset,
        data: dict[str, Any],
        cleaned: bool = True,
    ) -> Self:
        return cls(dataset, data, cleaned=cleaned)

    @classmethod
    def from_statements(
        cls,
        dataset: Dataset,
        statements: Iterable[Statement],
    ) -> Self:
        model = Model.instance()
        canonical_id: str | None = None
        schemata: set[str] = set()
        first_seens: set[str] = set()
        props: dict[str, set[Statement]] = {}
        for stmt in statements:
            schemata.add(stmt.schema)
            canonical_id = stmt.canonical_id or canonical_id or stmt.entity_id
            if stmt.prop == BASE_ID:
                if stmt.first_seen is not None:
                    first_seens.add(stmt.first_seen)
            else:
                if stmt.prop not in props:
                    props[stmt.prop] = set()
                props[stmt.prop].add(stmt)

        schema: Schema | None = None
        for name in schemata:
            if schema is None:
                schema = model.get(name)
            elif schema.name != name:
                try:
                    schema = model.common_schema(schema, name)
                except InvalidData as exc:
                    raise InvalidData(f"{canonical_id}: {exc}") from exc

        if schema is None:
            err = f"No valid schema for entity: {canonical_id} {schemata!r}"
            raise InvalidData(err)

        data = {"schema": schema, "id": canonical_id}
        obj = cls(dataset, data)
        obj.last_change = max(first_seens, default=None)
        obj._statements = dict(props)
        return obj
