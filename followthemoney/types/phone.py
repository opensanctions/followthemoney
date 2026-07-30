from functools import cache
from typing import TYPE_CHECKING, Optional

from phonenumbers import (
    SUPPORTED_REGIONS,
    PhoneNumber,
    PhoneNumberFormat,
    format_number,
    is_valid_number,
)
from phonenumbers import parse as parse_number
from phonenumbers.phonenumberutil import NumberParseException, region_code_for_number
from rigour.territories import get_territory

from followthemoney.exc import InvalidData
from followthemoney.types.common import PropertyType
from followthemoney.util import dampen
from followthemoney.util import defer as _

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


# TODO: for json schema export
# https://stackoverflow.com/questions/6478875/regular-expression-matching-e-164-formatted-phone-numbers


@cache
def _dialing_region(country: str) -> str:
    """Turn a country code into a region code that phone numbers can be dialed in.

    Accepts anything `rigour` recognises as a territory, including subdivisions
    like `gb-eng`, which resolve to their parent country. Territories that have
    no dialing plan of their own (`eu`, `zz`, historical states) are rejected.
    """
    territory = get_territory(country)
    if territory is not None:
        for code in (territory.code, territory.ftm_country):
            if code is not None and code.upper() in SUPPORTED_REGIONS:
                return code.upper()
    raise InvalidData(f"Not a valid country for a phone number: {country!r}")


def _parse_valid(number: str, region: str | None) -> PhoneNumber | None:
    """Parse a number as dialed in the given region, if it yields a valid number."""
    try:
        parsed = parse_number(number, region)
    except NumberParseException:
        return None
    if not is_valid_number(parsed):
        return None
    return parsed


class PhoneType(PropertyType):
    """A phone number in E.164 format, i.e. one that always carries an
    international dialing prefix (e.g. `+38760183628`).

    Source data often gives numbers in national format, without that prefix. Pass
    the country the number is dialed in as the `format` hint to have the prefix
    applied, e.g. `entity.add("phone", "017623423980", format="de")`. A number
    that is neither in international format nor accompanied by a hint is rejected."""

    name = "phone"
    group = "phones"
    label = _("Phone number")
    plural = _("Phone numbers")
    matchable = True
    pivot = True
    max_length = 64

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: Optional["EntityProxy"] = None,
    ) -> str | None:
        # Resolved up front so that an invalid hint is reported even when the
        # number turns out to be in international format already:
        region = None if format is None else _dialing_region(format)
        parsed = _parse_valid(text, None)
        if parsed is None and region is not None:
            parsed = _parse_valid(text, region)
        if parsed is None:
            return None
        return str(format_number(parsed, PhoneNumberFormat.E164))

    def country_hint(self, value: str) -> str | None:
        try:
            number = parse_number(value)
            code = region_code_for_number(number)
            if code is None:
                return None
            return str(code).lower()
        except NumberParseException:
            return None

    def _specificity(self, value: str) -> float:
        # TODO: insert artificial intelligence here.
        return dampen(7, 11, value)

    def node_id(self, value: str) -> str | None:
        return f"tel:{value}"

    def caption(self, value: str, format: str | None = None) -> str:
        try:
            number = parse_number(value)
            formatted = format_number(number, PhoneNumberFormat.INTERNATIONAL)
            return str(formatted)
        except NumberParseException:
            return value
