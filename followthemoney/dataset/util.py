from datetime import datetime, timezone
from typing import Annotated, Any

from normality import slugify_text
from pydantic import AfterValidator, BeforeValidator, HttpUrl, PlainSerializer
from rigour.time import datetime_iso

from followthemoney.types import registry


def dataset_name_check(value: str) -> str:
    """Check that the given value is a valid dataset name. This doesn't convert
    or clean invalid names, but raises an error if they are not compliant to
    force the user to fix an invalid name"""
    if slugify_text(value, sep="_") != value:
        raise ValueError("Invalid {}: {!r}".format("dataset name", value))
    return value


def type_check_date(value: Any) -> str:
    """Check that the given value is a valid date string."""
    cleaned = registry.date.clean(value)
    if cleaned is None:
        raise ValueError(f"Invalid date: {value!r}")
    return cleaned


PartialDate = Annotated[str, BeforeValidator(type_check_date)]


def type_check_country(value: Any) -> str:
    """Check that the given value is a valid country code."""
    cleaned = registry.country.clean(value)
    if cleaned is None:
        raise ValueError(f"Invalid country code: {value!r}")
    return cleaned


CountryCode = Annotated[str, BeforeValidator(type_check_country)]


def type_check_http_url(v: str) -> str:
    url = HttpUrl(v)
    return str(url)


Url = Annotated[str, AfterValidator(type_check_http_url)]


def serialize_dt(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    text = datetime_iso(dt)
    assert text is not None, f"Invalid datetime: {dt!r}"
    return text


DateTimeISO = Annotated[datetime, PlainSerializer(serialize_dt)]
