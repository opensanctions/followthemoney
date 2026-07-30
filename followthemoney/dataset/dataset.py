import logging
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, TypeVar

import yaml
from pydantic import BaseModel, field_validator, model_validator

from followthemoney.dataset.coverage import DataCoverage
from followthemoney.dataset.publisher import DataPublisher
from followthemoney.dataset.resource import DataResource
from followthemoney.dataset.util import DateTimeISO, Url, dataset_name_check
from followthemoney.util import PathLike

if TYPE_CHECKING:
    from followthemoney.dataset.catalog import DataCatalog

DS = TypeVar("DS", bound="Dataset")

log = logging.getLogger(__name__)


class DatasetModel(BaseModel):
    name: str
    title: str
    license: Url | None = None
    summary: str | None = None
    description: str | None = None
    url: Url | None = None
    updated_at: DateTimeISO | None = None
    last_export: DateTimeISO | None = None
    entity_count: int | None = None
    thing_count: int | None = None
    version: str | None = None
    category: str | None = None
    tags: list[str] = []
    publisher: DataPublisher | None = None
    coverage: DataCoverage | None = None
    resources: list[DataResource] = []
    children: set[str] = set()
    deprecation: str | None = None
    deprecated: bool = False

    @field_validator("name", mode="after")
    @classmethod
    def check_name(cls, value: str) -> str:
        return dataset_name_check(value)

    @model_validator(mode="before")
    @classmethod
    def ensure_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "name" not in data:
                raise ValueError("Missing dataset name")
            data["title"] = data.get("title", data["name"])
            children = set(data.get("children", []))
            children.update(data.get("datasets", []))
            children.update(data.get("scopes", []))
            data["children"] = children
        return data

    @model_validator(mode="after")
    def evaluate_data(self) -> "DatasetModel":
        # derive deprecated from deprecation notice:
        if self.deprecation is not None:
            self.deprecation = self.deprecation.strip()
            if len(self.deprecation) == 0:
                self.deprecation = None
        self.deprecated = self.deprecation is not None or self.deprecated
        if self.deprecated and (self.coverage is None or self.coverage.end is None):
            raise ValueError("Deprecated dataset coverage must have an end date.")
        return self

    def get_resource(self, name: str) -> DataResource:
        for res in self.resources:
            if res.name == name:
                return res
        raise ValueError(f"No resource named {name!r}!")


class Dataset:
    """A container for entities, often from one source or related to one topic.
    A dataset is a set of data, sez W3C."""

    UNDEFINED = "undefined"

    def __init__(self: Self, data: dict[str, Any]) -> None:
        self.model = DatasetModel.model_validate(data)
        self.name = self.model.name
        self.children: set[Self] = set()

    @cached_property
    def is_collection(self: Self) -> bool:
        return len(self.model.children) > 0

    @property
    def datasets(self: Self) -> set[Self]:
        current: set[Self] = {self}
        for child in self.children:
            current.update(child.datasets)
        return current

    @property
    def dataset_names(self: Self) -> list[str]:
        return [d.name for d in self.datasets]

    @property
    def leaves(self: Self) -> set[Self]:
        """All contained datasets which are not collections (can be 'self')."""
        return {d for d in self.datasets if not d.is_collection}

    @property
    def leaf_names(self: Self) -> set[str]:
        return {d.name for d in self.leaves}

    def __hash__(self) -> int:
        return hash(repr(self))

    def __repr__(self) -> str:
        if not hasattr(self, "name"):
            return "<Dataset>"
        return f"<Dataset({self.name})>"  # pragma: no cover

    def get_resource(self, name: str) -> DataResource:
        for res in self.model.resources:
            if res.name == name:
                return res
        raise ValueError(f"No resource named {name!r}!")

    def to_dict(self) -> dict[str, Any]:
        """Convert the dataset to a dictionary representation."""
        return self.model.model_dump(mode="json", exclude_none=True)

    @classmethod
    def from_path(
        cls, path: PathLike, catalog: "DataCatalog[Self] | None" = None
    ) -> Self:
        from followthemoney.dataset.catalog import DataCatalog

        path = Path(path)
        with open(path, "r") as fh:
            data = yaml.safe_load(fh)
            if catalog is None:
                catalog = DataCatalog(cls, {})
            if "name" not in data:
                data["name"] = path.stem
            return catalog.make_dataset(data)

    @classmethod
    def make(cls, data: dict[str, Any]) -> Self:
        from followthemoney.dataset.catalog import DataCatalog

        catalog = DataCatalog(cls, {})
        return catalog.make_dataset(data)

    def __eq__(self, other: Any) -> bool:
        try:
            return bool(self.name == other.name)
        except AttributeError:
            return False

    def __lt__(self, other: Any) -> bool:
        return self.name.__lt__(other.name)
