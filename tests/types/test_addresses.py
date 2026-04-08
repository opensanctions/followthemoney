from followthemoney.types import registry

UK = """43 Duke Street
Edinburgh
EH6 8HH"""


def test_clean():
    addresses = registry.address
    assert addresses.clean(UK) == "43 Duke Street, Edinburgh, EH6 8HH"
    assert addresses.clean("huhu\n   haha") == "huhu, haha"
    assert addresses.clean("huhu,\n haha") == "huhu, haha"


def test_compare():
    addresses = registry.address
    # Similar addresses should score high
    score = addresses.compare(
        "43 Duke Street, Edinburgh, EH6 8HH",
        "43 Duke St, Edinburgh, EH6 8HH",
    )
    assert score > 0.5
    # Completely different addresses should score low
    score = addresses.compare(
        "43 Duke Street, Edinburgh, EH6 8HH",
        "1600 Pennsylvania Avenue, Washington DC",
    )
    assert score < 0.3
    # Non-normalizable input
    assert addresses.compare("", "43 Duke Street") == 0.0


def test_node_id():
    addresses = registry.address
    node = addresses.node_id("43 Duke Street, Edinburgh, EH6 8HH")
    assert node is not None
    assert node.startswith("addr:")
    # Same address should produce same node_id
    assert node == addresses.node_id("43 Duke Street, Edinburgh EH6 8HH")
    # Empty/garbage should return None
    assert addresses.node_id("") is None


def test_specificity():
    addresses = registry.address
    assert addresses.specificity(UK) > 0.2
    assert addresses.specificity("London") < 0.2
