from typing import TYPE_CHECKING, Any

from followthemoney.entity import ValueEntity
from followthemoney.exc import InvalidMapping
from followthemoney.mapping.csv import CSVSource
from followthemoney.mapping.entity import EntityMapping
from followthemoney.mapping.source import Record, Source
from followthemoney.mapping.sql import SQLSource
from followthemoney.proxy import EntityProxy

if TYPE_CHECKING:
    from followthemoney.model import Model


class QueryMapping:
    __slots__ = ("model", "data", "refs", "entities", "source")

    def __init__(
        self,
        model: "Model",
        data: dict[str, Any],
        key_prefix: str | None = None,
        dataset: str | None = None,
    ) -> None:
        self.model = model
        self.refs: set[str] = set()
        self.entities: list[EntityMapping] = []
        for name, edata in data.get("entities", {}).items():
            entity = EntityMapping(
                model, self, name, edata, key_prefix=key_prefix, dataset=dataset
            )

            self.entities.append(entity)
            self.refs.update(entity.refs)

        if len(self.entities) == 0:
            raise InvalidMapping("No entity mappings are defined.")

        # Check if the provided links satisfy the ranges of the given
        # properties (e.g. the owner of a company must be a legal person)
        for entity in self.entities:
            entity.bind()

        # Do dependency resolution, i.e. find the right order to
        # map these entities. This is needed to resolve entity IDs
        # in dependent entities.
        entities = self.entities
        self.entities = []
        resolved: set[str] = set()
        while len(entities) > 0:
            before = len(entities)
            for entity in entities:
                if entity.dependencies.issubset(resolved):
                    self.entities.append(entity)
                    entities.remove(entity)
                    resolved.add(entity.name)
                    break
            if before == len(entities):
                raise InvalidMapping("Circular entity dependency detected.")

        self.source = self._get_source(data)

    def _get_source(self, data: dict[str, Any]) -> Source:
        if "database" in data:
            return SQLSource(self, data)
        if "csv_url" in data or "csv_urls" in data:
            return CSVSource(self, data)
        raise InvalidMapping("Cannot determine mapping type: %r" % data)

    def map(self, record: Record) -> dict[str, ValueEntity]:
        data: dict[str, EntityProxy] = {}
        result: dict[str, ValueEntity] = {}
        for entity in self.entities:
            mapped = entity.map(record, data)
            if mapped is not None:
                data[entity.name] = mapped
                result[entity.name] = mapped
        return result
