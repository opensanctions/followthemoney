"""Dataset filter DSL — JSON AST evaluation.

Provides ``evaluate_query(catalog, query)`` to filter datasets using a recursive
JSON structure with ``or``, ``and``, and ``not`` operators. Leaf values are
dataset names, collection names (expanded to leaves), or ``#tag`` selectors.

See https://followthemoney.tech/docs/metadata/#dataset-query-dsl for full
documentation and examples.
"""

from typing import Any, Dict, List, Set, TYPE_CHECKING, Union

from followthemoney.dataset.dataset import DS
from followthemoney.exc import InvalidDatasetQuery

if TYPE_CHECKING:
    from followthemoney.dataset.catalog import DataCatalog

DatasetQuery = Union[str, List[Any], Dict[str, Any]]

OPERATORS = frozenset(("or", "and", "not"))


def validate_query(query: Any) -> None:
    """Check that a query conforms to the DSL grammar. Raises InvalidDatasetQuery on failure."""
    if isinstance(query, str):
        if len(query) == 0:
            raise InvalidDatasetQuery("Empty string in query")
        return
    if isinstance(query, list):
        if len(query) == 0:
            raise InvalidDatasetQuery("Empty array in query")
        for item in query:
            validate_query(item)
        return
    if isinstance(query, dict):
        if len(query) != 1:
            raise InvalidDatasetQuery("Operator object must have exactly one key")
        key = next(iter(query))
        if key not in OPERATORS:
            raise InvalidDatasetQuery("Unknown operator: %r" % key)
        value = query[key]
        if key == "not":
            validate_query(value)
        else:
            if not isinstance(value, list) or len(value) == 0:
                raise InvalidDatasetQuery("Operator %r requires a non-empty array" % key)
            for item in value:
                validate_query(item)
        return
    raise InvalidDatasetQuery("Invalid query node type: %s" % type(query).__name__)


def _resolve_leaf(catalog: "DataCatalog[DS]", leaf: str) -> Set[DS]:
    """Resolve a leaf string to a set of leaf datasets."""
    if leaf.startswith("#"):
        tag = leaf[1:]
        result: Set[DS] = set()
        for ds in catalog.datasets:
            if tag in ds.model.tags:
                result.update(ds.leaves)
        return result
    dataset = catalog.get(leaf)
    if dataset is None:
        raise InvalidDatasetQuery("Unknown dataset: %r" % leaf)
    return dataset.leaves


def _universe(catalog: "DataCatalog[DS]") -> Set[DS]:
    """Return all leaf datasets in the catalog."""
    result: Set[DS] = set()
    for ds in catalog.datasets:
        if not ds.is_collection:
            result.add(ds)
    return result


def _evaluate(catalog: "DataCatalog[DS]", query: DatasetQuery) -> Set[DS]:
    """Recursively evaluate a query AST against a catalog."""
    if isinstance(query, str):
        return _resolve_leaf(catalog, query)
    if isinstance(query, list):
        result: Set[DS] = set()
        for item in query:
            result.update(_evaluate(catalog, item))
        return result
    if isinstance(query, dict):
        key = next(iter(query))
        value = query[key]
        if key == "or":
            result = set()
            for item in value:
                result.update(_evaluate(catalog, item))
            return result
        if key == "and":
            result = _evaluate(catalog, value[0])
            for item in value[1:]:
                result = result & _evaluate(catalog, item)
            return result
        if key == "not":
            return _universe(catalog) - _evaluate(catalog, value)
    raise InvalidDatasetQuery("Invalid query node type: %s" % type(query).__name__)


def evaluate_query(catalog: "DataCatalog[DS]", query: DatasetQuery) -> Set[DS]:
    """Evaluate a query AST against a catalog, returning matching leaf datasets.

    The query is a JSON-like structure using "or", "and", and "not" operators.
    Leaf strings are dataset names, collection names, or "#tag" selectors.
    A bare list is treated as an implicit "or".
    """
    validate_query(query)
    return _evaluate(catalog, query)
