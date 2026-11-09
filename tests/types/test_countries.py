from collections.abc import Sequence
from statistics import mean

from followthemoney.types import registry


def test_country_codes():
    countries = registry.country
    assert countries.clean("DE") == "de"
    assert countries.validate("DE")
    assert not countries.validate("DEU")
    assert not countries.validate("")
    assert not countries.validate(None)
    assert not countries.validate(4)
    assert not countries.validate("SU")
    assert countries.validate("XK")
    assert countries.validate("EU")

    assert countries.country_hint("eu") == "eu"
    assert "country:eu" == countries.node_id("eu")


def test_country_names():
    countries = registry.country
    assert countries.clean(None) is None
    assert countries.clean("Takatukaland", fuzzy=False) is None
    assert countries.clean("Germany") == "de"
    # assert countries.clean('Germani') == 'de'
    assert countries.clean("Soviet Union") == "suhh"


def test_country_set_reducers() -> None:
    countries = registry.country
    left = ["de", "fr"]
    right = ["de", "fr"]
    assert countries.compare_sets(left, right) == 1.0
    assert countries.compare_sets(left, right, func=min) == 0.0
    assert countries.compare_sets(left, right, func=mean) == 0.5
    assert countries.compare_sets(left, right, func=sum) == 2.0
    assert countries.compare_sets([], right, func=mean) == 0.0
    assert countries.compare_sets(left, [], func=mean) == 0.0
    assert countries.compare_sets(["de", "de"], ["de"], func=sum) == 2.0
    assert countries.compare_sets(["as", "de"], ["us"], func=mean) == 0.5

    observed: list[float] = []

    def record_scores(scores: Sequence[float]) -> float:
        observed.extend(scores)
        return 0.25

    assert countries.compare_sets(left, right, func=record_scores) == 0.25
    assert observed == [1.0, 0.0, 0.0, 1.0]
