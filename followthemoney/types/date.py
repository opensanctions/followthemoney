import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from prefixdate import Precision, parse, parse_format

from followthemoney.types.common import PropertyType
from followthemoney.util import dampen
from followthemoney.util import defer as _

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


class DateType(PropertyType):
    """A date or time stamp. This is based on ISO 8601, but meant to allow for different
    degrees of precision by specifying a prefix. This means that `2021`, `2021-02`,
    `2021-02-16`, `2021-02-16T21`, `2021-02-16T21:48` and `2021-02-16T21:48:52`
    are all valid values, with an implied precision.

    The timezone is always expected to be UTC and cannot be specified otherwise. There is
    no support for calendar weeks (`2021-W7`) and date ranges (`2021-2024`)."""

    name = "date"
    group = "dates"
    label = _("Date")
    plural = _("Dates")
    matchable = True
    max_length = 32

    HISTORIC = "1001-01-01"
    """A sentinel date value representing a very old date, used to indicate historic (and often imprecise) dates
    that can be assumed to be long in the past."""

    RELEVANCE_MIN = "1900-01-01"
    """A cutoff date value representing the minimum relevant date for modern fincrime applications."""

    RELEVANCE_MAX = "2100-12-31"
    """A cutoff date value representing the maximum relevant date for modern fincrime applications."""

    def validate(
        self, value: str, fuzzy: bool = False, format: str | None = None
    ) -> bool:
        """Check if a thing is a valid date."""
        if format is not None:
            prefix = parse_format(value, format)
        else:
            prefix = parse(value)
        return prefix.precision != Precision.EMPTY

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        """The classic: date parsing, every which way."""
        if format is not None:
            return parse_format(text, format).text
        return parse(text).text

    def _specificity(self, value: str) -> float:
        return dampen(5, 13, value)

    def compare(self, left: str, right: str) -> float:
        prefix = os.path.commonprefix([left, right])
        return dampen(4, 10, prefix)

    def to_datetime(self, value: str) -> datetime | None:
        """Convert a date string to a datetime object in UTC for handling in Python. This
        will convert the unset fields beyond the prefix to the first possible value, e.g.
        `2021-02` will become `2021-02-01T00:00:00Z`.

        Args:
            value (str): The date string to convert.

        Returns:
            datetime | None: The parsed datetime object in UTC, or None if parsing fails.
        """
        return parse(value).dt

    def to_number(self, value: str) -> float | None:
        """Convert a date string to a number, which is the number of seconds since the epoch
        (1970-01-01T00:00:00Z).

        Args:
            value (str): The date string to convert.

        Returns:
            float | None: The timestamp as a float, or None if parsing fails.
        """
        date = self.to_datetime(value)
        if date is None:
            return None
        # We make a best effort all over the app to ensure all times are in UTC.
        if date.tzinfo is None:
            date = date.replace(tzinfo=UTC)
        return date.timestamp()
