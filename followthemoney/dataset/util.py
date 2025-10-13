from datetime import datetime
from normality import slugify_text
from typing import Annotated, Any
from rigour.time import datetime_iso
from pydantic import AfterValidator, BeforeValidator, HttpUrl, PlainSerializer

from followthemoney.types import registry


def dataset_name_check(value: str) -> str:
    """Check that the given value is a valid dataset name. This doesn't convert
    or clean invalid names, but raises an error if they are not compliant to
    force the user to fix an invalid name"""
    if slugify_text(value, sep="_") != value:
        raise ValueError("Invalid %s: %r" % ("dataset name", value))
    return value


def type_check_date(value: Any) -> str:
    """Check that the given value is a valid date string."""
    cleaned = registry.date.clean(value)
    if cleaned is None:
        raise ValueError("Invalid date: %r" % value)
    return cleaned


PartialDate = Annotated[str, BeforeValidator(type_check_date)]


def type_check_country(value: Any) -> str:
    """Check that the given value is a valid country code."""
    cleaned = registry.country.clean(value)
    if cleaned is None:
        raise ValueError("Invalid country code: %r" % value)
    return cleaned


CountryCode = Annotated[str, BeforeValidator(type_check_country)]


def type_check_http_url(v: str) -> str:
    url = HttpUrl(v)
    return str(url)


Url = Annotated[str, AfterValidator(type_check_http_url)]


def serialize_dt(dt: datetime) -> str:
    text = datetime_iso(dt)
    assert text is not None, "Invalid datetime: %r" % dt
    return text


DateTimeISO = Annotated[datetime, PlainSerializer(serialize_dt)]
