from followthemoney.types import registry


def test_topic_country_codes():
    topics = registry.topic
    assert topics.clean("role.pep") == "role.pep"
    assert topics.clean("role.PEP") == "role.pep"
    assert topics.clean("banana") is None
    assert topics.clean(None) is None
    assert topics.validate("role.pep") is True
    assert topics.validate("role.PEP") is True
    assert topics.validate("DEU") is False
    assert topics.validate("") is False
    assert topics.validate(None) is False
    assert "topic:role.pep" in topics.node_id("role.pep")


def test_topic_risks():
    topics = registry.topic
    assert topics.validate("corp.clone") is True
    assert "corp.clone" in topics.RISKS
    assert "corp.public" not in topics.RISKS
    assert topics.RISKS.issubset(topics._TOPICS)


def test_topic_geo_risk():
    topics = registry.topic
    assert topics.clean("geo.risk") == "geo.risk"
    assert "geo.risk" in topics.names
    assert "geo.risk" in topics.RISKS
