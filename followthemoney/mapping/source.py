from collections.abc import Generator
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from followthemoney.mapping.query import QueryMapping

Filter = set[str | None]
Record = dict[str, str]


class Source(object):
    def __init__(self, query: "QueryMapping", data: dict[str, Any]) -> None:
        self.query = query
        self.filters = cast(dict[str, Any], data.get("filters", {})).items()
        self.filters_not = cast(dict[str, Any], data.get("filters_not", {})).items()

    @property
    def records(self) -> Generator[Record, None, None]:
        raise NotImplementedError

    def __len__(self) -> int:
        return 0
