from followthemoney.value import string_list
from followthemoney import model
from followthemoney.proxy import EntityProxy


def test_string_list():
    assert string_list("test") == ["test"]
    assert string_list("") == []
    assert string_list(b"test") == ["test"]
    assert string_list(123) == ["123"]
    assert string_list(45.67) == ["45.67"]
    assert string_list(True) == ["true"]
    assert string_list(False) == ["false"]
    assert string_list(None) == []
    assert string_list(["a", "b", "c"]) == ["a", "b", "c"]
    assert string_list(["", "b", "c"]) == ["b", "c"]
    assert string_list({"id": "entity1"}) == ["entity1"]
    assert string_list({"id": None}) == []
    assert string_list({"name": "entity2"}) == []
    schema = model.get("Person")
    assert schema is not None
    proxy = EntityProxy(schema, {})
    assert string_list(proxy) == []
    proxy.id = "entity3"
    assert string_list(proxy) == ["entity3"]
