from typing import Any, Dict, List, Optional, Set, TypeVar

from rigour.names import pick_name

from followthemoney.proxy import EntityProxy
from followthemoney.schema import Schema
from followthemoney.statement import BASE_ID, Statement

VE = TypeVar("VE", bound="ValueEntity")


def _defined(*args: Optional[str]) -> List[str]:
    return [arg for arg in args if arg is not None]


class ValueEntity(EntityProxy):
    """
    This class has the extended attributes from `StatementEntity` but without
    statements. Useful for streaming around. Starting from followthemoeny 4.0,
    applications should use this entity class as the base class.
    """

    def __init__(
        self,
        schema: Schema,
        data: Dict[str, Any],
        key_prefix: Optional[str] = None,
        cleaned: bool = True,
    ):
        super().__init__(schema, data, key_prefix=key_prefix, cleaned=cleaned)
        self._caption: Optional[str] = data.get("caption")
        self.datasets: Set[str] = set(data.get("datasets", []))
        self.referents: Set[str] = set(data.get("referents", []))
        self.first_seen: Optional[str] = data.get("first_seen")
        self.last_seen: Optional[str] = data.get("last_seen")
        self.last_change: Optional[str] = data.get("last_change")

        # add data from statement dict if present.
        # this updates the dataset and referents set
        for stmt_data in data.pop("statements", []):
            stmt = Statement.from_dict(stmt_data)
            self.datasets.add(stmt.dataset)
            if stmt.schema != self.schema.name:
                self.schema = schema.model.common_schema(self.schema, stmt.schema)
            if stmt.entity_id != self.id:
                self.referents.add(stmt.entity_id)
            if stmt.prop != BASE_ID:
                self.add(stmt.prop, stmt.value)

    def merge(self: VE, other: EntityProxy) -> VE:
        merged = super().merge(other)
        if isinstance(other, ValueEntity):
            merged._caption = pick_name(_defined(self._caption, other._caption))
            merged.referents.update(other.referents)
            merged.datasets.update(other.datasets)
            merged.first_seen = min(
                _defined(self.first_seen, other.first_seen), default=None
            )
            merged.last_seen = max(
                _defined(self.last_seen, other.last_seen), default=None
            )
            changed = _defined(self.last_change, other.last_change)
            merged.last_change = max(changed, default=None)
        return merged

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "caption": self._caption or self.caption,
            "schema": self.schema.name,
            "properties": self.properties,
            "referents": list(self.referents),
            "datasets": list(self.datasets),
        }
        if self.first_seen is not None:
            data["first_seen"] = self.first_seen
        if self.last_seen is not None:
            data["last_seen"] = self.last_seen
        if self.last_change is not None:
            data["last_change"] = self.last_change
        return data
