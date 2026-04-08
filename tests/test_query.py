import pytest
from followthemoney.dataset import Dataset, DataCatalog
from followthemoney.dataset.query import evaluate_query, validate_query
from followthemoney.exc import InvalidDatasetQuery


def make_catalog():
    """Build a small catalog with datasets, collections, and tags."""
    catalog = DataCatalog(Dataset, {})
    catalog.make_dataset(
        {"name": "us_ofac_sdn", "title": "US OFAC SDN", "tags": ["list.sanction", "issuer.us", "issuer.west"]}
    )
    catalog.make_dataset(
        {"name": "eu_fsf", "title": "EU Financial Sanctions", "tags": ["list.sanction", "issuer.eu", "issuer.west"]}
    )
    catalog.make_dataset(
        {"name": "gb_hmt", "title": "UK HMT Sanctions", "tags": ["list.sanction", "issuer.gb", "issuer.west"]}
    )
    catalog.make_dataset(
        {"name": "ru_fedsfm", "title": "Russia Fedsfm", "tags": ["list.sanction", "issuer.ru"]}
    )
    catalog.make_dataset(
        {"name": "lt_fiu", "title": "Lithuania FIU", "tags": ["list.sanction", "issuer.west"]}
    )
    catalog.make_dataset(
        {"name": "world_bank_debarred", "title": "World Bank Debarred", "tags": ["list.debarment", "issuer.west"]}
    )
    catalog.make_dataset(
        {"name": "sanctions", "title": "All Sanctions", "children": ["us_ofac_sdn", "eu_fsf", "gb_hmt", "ru_fedsfm", "lt_fiu"]}
    )
    return catalog


@pytest.fixture
def catalog():
    return make_catalog()


def names(result):
    return {d.name for d in result}


def test_resolve_single_dataset(catalog):
    result = evaluate_query(catalog, "us_ofac_sdn")
    assert names(result) == {"us_ofac_sdn"}


def test_resolve_collection_expands_to_leaves(catalog):
    result = evaluate_query(catalog, "sanctions")
    assert names(result) == {"us_ofac_sdn", "eu_fsf", "gb_hmt", "ru_fedsfm", "lt_fiu"}


def test_resolve_tag_selector(catalog):
    result = evaluate_query(catalog, "#issuer.eu")
    assert names(result) == {"eu_fsf"}


def test_resolve_tag_multiple_matches(catalog):
    result = evaluate_query(catalog, "#list.sanction")
    assert names(result) == {"us_ofac_sdn", "eu_fsf", "gb_hmt", "ru_fedsfm", "lt_fiu"}


def test_resolve_unknown_dataset_raises(catalog):
    with pytest.raises(InvalidDatasetQuery, match="Unknown dataset"):
        evaluate_query(catalog, "nonexistent")


def test_resolve_tag_no_matches(catalog):
    result = evaluate_query(catalog, "#issuer.cn")
    assert result == set()


def test_operator_or(catalog):
    result = evaluate_query(catalog, {"or": ["us_ofac_sdn", "eu_fsf"]})
    assert names(result) == {"us_ofac_sdn", "eu_fsf"}


def test_operator_and(catalog):
    result = evaluate_query(catalog, {"and": ["#issuer.west", "#list.sanction"]})
    assert names(result) == {"us_ofac_sdn", "eu_fsf", "gb_hmt", "lt_fiu"}


def test_operator_not(catalog):
    result = evaluate_query(catalog, {"not": "ru_fedsfm"})
    assert "ru_fedsfm" not in names(result)
    assert "us_ofac_sdn" in names(result)
    assert "world_bank_debarred" in names(result)


def test_bare_array_is_implicit_or(catalog):
    result = evaluate_query(catalog, ["us_ofac_sdn", "eu_fsf"])
    assert names(result) == {"us_ofac_sdn", "eu_fsf"}


def test_and_with_not_for_subtraction(catalog):
    """(#issuer.west & #list.sanction) - lt_fiu"""
    result = evaluate_query(catalog, {
        "and": [
            {"or": ["#issuer.west", "#list.sanction"]},
            {"not": "lt_fiu"},
        ]
    })
    assert "lt_fiu" not in names(result)
    assert "us_ofac_sdn" in names(result)


def test_western_sanctions_minus_exclusions(catalog):
    """(#issuer.west|#list.sanction|#list.debarment)-lt_fiu-#issuer.ru"""
    result = evaluate_query(catalog, {
        "and": [
            {"or": ["#issuer.west", "#list.sanction", "#list.debarment"]},
            {"not": "lt_fiu"},
            {"not": "#issuer.ru"},
        ]
    })
    assert names(result) == {"us_ofac_sdn", "eu_fsf", "gb_hmt", "world_bank_debarred"}


def test_nested_or_inside_not(catalog):
    """Exclude multiple datasets via not(or(...))"""
    result = evaluate_query(catalog, {
        "and": [
            "#list.sanction",
            {"not": {"or": ["lt_fiu", "ru_fedsfm"]}},
        ]
    })
    assert names(result) == {"us_ofac_sdn", "eu_fsf", "gb_hmt"}


def test_collection_name_in_and_with_tag(catalog):
    """Use a collection name alongside a tag in and."""
    result = evaluate_query(catalog, {"and": ["sanctions", "#issuer.west"]})
    assert names(result) == {"us_ofac_sdn", "eu_fsf", "gb_hmt", "lt_fiu"}


def test_validate_query_rejects_empty_string():
    with pytest.raises(InvalidDatasetQuery, match="Empty string"):
        validate_query("")


def test_validate_query_rejects_empty_array():
    with pytest.raises(InvalidDatasetQuery, match="Empty array"):
        validate_query([])


def test_validate_query_rejects_unknown_operator():
    with pytest.raises(InvalidDatasetQuery, match="Unknown operator"):
        validate_query({"xor": ["a", "b"]})


def test_validate_query_rejects_multiple_keys():
    with pytest.raises(InvalidDatasetQuery, match="exactly one key"):
        validate_query({"or": ["a"], "and": ["b"]})


def test_validate_query_rejects_or_without_array():
    with pytest.raises(InvalidDatasetQuery, match="non-empty array"):
        validate_query({"or": "a"})


def test_validate_query_rejects_invalid_type():
    with pytest.raises(InvalidDatasetQuery, match="Invalid query node type"):
        validate_query(42)


def test_validate_query_accepts_complex_query():
    validate_query({
        "and": [
            {"or": ["#issuer.west", "#list.sanction"]},
            {"not": "lt_fiu"},
        ]
    })
