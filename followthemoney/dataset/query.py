"""Dataset filter DSL — AST evaluation.

Provides ``evaluate_query(catalog, query)`` to filter datasets using a recursive
dictionary structure with ``or``, ``and``, and ``not`` operators. Leaf values are
dataset names, collection names (expanded to leaves), or ``#tag`` selectors.

See https://followthemoney.tech/docs/metadata/#dataset-query-dsl for full
documentation and examples.
"""

from collections.abc import Mapping, Sequence
import functools
from typing import Any, TYPE_CHECKING

from followthemoney.dataset.dataset import DS
from followthemoney.exc import InvalidDatasetQuery

if TYPE_CHECKING:
    from followthemoney.dataset.catalog import DataCatalog

DatasetQuery = str | list[Any] | dict[str, Any]

OPERATORS = frozenset(("or", "and", "not"))


def validate_query(query: Any) -> None:
    """Check that a query conforms to the DSL grammar. Raises InvalidDatasetQuery on failure."""
    if isinstance(query, str):
        if len(query) == 0:
            raise InvalidDatasetQuery("Empty string in query")
        return
    if isinstance(query, Sequence):
        if len(query) == 0:
            raise InvalidDatasetQuery("Empty array in query")
        for item in query:
            validate_query(item)
        return
    if isinstance(query, Mapping):
        if len(query) != 1:
            raise InvalidDatasetQuery("Operator object must have exactly one key")
        key = next(iter(query))
        if key not in OPERATORS:
            raise InvalidDatasetQuery("Unknown operator: %r" % key)
        value = query[key]
        if key == "not":
            validate_query(value)
        else:
            if not isinstance(value, Sequence) or isinstance(value, str) or len(value) == 0:
                raise InvalidDatasetQuery(
                    "Operator %r requires a non-empty array" % key
                )
            for item in value:
                validate_query(item)
        return
    raise InvalidDatasetQuery("Invalid query node type: %s" % type(query).__name__)


def _resolve_leaf(catalog: "DataCatalog[DS]", leaf: str) -> set[DS]:
    """Resolve a leaf string to a set of leaf datasets."""
    if leaf.startswith("#"):
        tag = leaf[1:]
        result: set[DS] = set()
        for ds in catalog.datasets:
            if tag in ds.model.tags:
                result.update(ds.leaves)
        return result
    dataset = catalog.get(leaf)
    if dataset is None:
        raise InvalidDatasetQuery("Unknown dataset: %r" % leaf)
    return dataset.leaves


def _universe(catalog: "DataCatalog[DS]") -> set[DS]:
    """Return all leaf datasets in the catalog."""
    result: set[DS] = set()
    for ds in catalog.datasets:
        if not ds.is_collection:
            result.add(ds)
    return result


def _evaluate(catalog: "DataCatalog[DS]", query: DatasetQuery) -> set[DS]:
    """Recursively evaluate a query AST against a catalog."""
    if isinstance(query, str):
        return _resolve_leaf(catalog, query)
    if isinstance(query, Sequence):
        result: set[DS] = set()
        for item in query:
            result.update(_evaluate(catalog, item))
        return result
    if isinstance(query, Mapping):
        key = next(iter(query))
        value = query[key]
        if key == "or":
            results = [_evaluate(catalog, item) for item in value]
            return functools.reduce(set.union, results)
        if key == "and":
            results = [_evaluate(catalog, item) for item in value]
            return functools.reduce(set.intersection, results)
        if key == "not":
            return _universe(catalog) - _evaluate(catalog, value)
    raise InvalidDatasetQuery("Invalid query node type: %s" % type(query).__name__)


def evaluate_query(catalog: "DataCatalog[DS]", query: DatasetQuery) -> set[DS]:
    """Evaluate a query AST against a catalog, returning matching leaf datasets.

    The query is a dictionary-like structure using "or", "and", and "not" operators.
    Leaf strings are dataset names, collection names, or "#tag" selectors.
    A bare list is treated as an implicit "or".
    """
    validate_query(query)
    return _evaluate(catalog, query)


def _match(query: DatasetQuery, datasets: set[str]) -> bool:
    """Recursively match a query AST against a set of dataset names."""
    if isinstance(query, str):
        if query.startswith("#"):
            raise InvalidDatasetQuery("Tag selectors require a catalog: %r" % query)
        return query in datasets
    if isinstance(query, Sequence):
        return any(_match(item, datasets) for item in query)
    if isinstance(query, Mapping):
        key = next(iter(query))
        value = query[key]
        if key == "or":
            return any(_match(item, datasets) for item in value)
        if key == "and":
            return all(_match(item, datasets) for item in value)
        if key == "not":
            return not _match(value, datasets)
    raise InvalidDatasetQuery("Invalid query node type: %s" % type(query).__name__)


def match_datasets(query: DatasetQuery, datasets: set[str]) -> bool:
    """Test whether a set of dataset names matches a query.

    Like ``evaluate_query`` but works against plain name strings instead of
    a full catalog. Tag selectors (``#...``) are not supported.

    The caller is responsible for validating the query once upfront via
    ``validate_query`` or ``parse_query`` (which produces valid ASTs by
    construction). This function skips validation so it can be used in
    tight loops over millions of entities.
    """
    return _match(query, datasets)
