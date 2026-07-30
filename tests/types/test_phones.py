import pytest

from followthemoney import model
from followthemoney.exc import InvalidData
from followthemoney.types import registry


def test_us_number():
    phones = registry.phone
    assert phones.clean("+1-800-784-2433") == "+18007842433"
    assert phones.clean("+1 800 784 2433") == "+18007842433"
    assert phones.clean("+18007842433") == "+18007842433"
    assert phones.clean("+1 555 8379") is None

    assert phones.validate("+18007842433") is True
    assert phones.validate("banana") is False


def test_country_format_hint():
    phones = registry.phone
    assert phones.clean("017623423980") is None
    assert phones.clean("017623423980", format="de") == "+4917623423980"
    assert phones.clean("017623423980", format="DE") == "+4917623423980"
    assert phones.clean("017623423980", format="deu") == "+4917623423980"
    # A subdivision resolves to the country it dials through:
    assert phones.clean("020 8366 1177", format="gb-eng") == "+442083661177"
    # An international number is not affected by a hint:
    assert phones.clean("+4917623423980", format="us") == "+4917623423980"
    # A hint does not rescue a number that is invalid in that country:
    assert phones.clean("017623423980", format="us") is None


def test_validate_honours_format():
    phones = registry.phone
    assert phones.validate("017623423980") is False
    assert phones.validate("017623423980", format="de") is True


def test_invalid_format_hint():
    phones = registry.phone
    # Junk, and territories that have no dialing plan of their own:
    for hint in ("banana", "xx", "eu", "zz", "suhh"):
        with pytest.raises(InvalidData):
            phones.clean("017623423980", format=hint)
    # Reported even when the number would be accepted without the hint:
    with pytest.raises(InvalidData):
        phones.clean("+4917623423980", format="banana")


def test_entity_add_with_format():
    entity = model.make_entity("Person")
    entity.add("phone", "017623423980", format="de")
    assert entity.get("phone") == ["+4917623423980"]

    # The hint stands on its own, whatever countries the entity carries:
    other = model.make_entity("Person")
    other.add("phone", "017623423980", format="de")
    other.add("country", "gb")
    assert other.get("phone") == ["+4917623423980"]


def test_entity_countries_are_not_used():
    phones = registry.phone
    proxy = model.make_entity("Person")
    proxy.add("country", "DE")
    assert phones.clean("017623423980", proxy=proxy) is None
    assert phones.clean("017623423980", format="de", proxy=proxy) == "+4917623423980"

    # No country-type property rescues a number in national format, whichever
    # one carries the country:
    entity = model.make_entity("Person")
    entity.add("country", "de")
    entity.add("birthCountry", "de")
    entity.add("phone", "017623423980")
    assert entity.get("phone") == []


def test_specificity():
    phones = registry.phone
    assert phones.specificity("+4917623423980") == 1


def test_country_hint():
    phones = registry.phone
    assert phones.country_hint("+4917623423980") == "de"
    assert phones.country_hint(None) is None
