import re
from functools import cache

from followthemoney.types.common import PropertyType
from followthemoney.util import defer as _


@cache
def _number_pattern(decimal: str, separator: str) -> re.Pattern[str]:
    """Build a strict, fully-anchored number+unit pattern for a given locale.

    A separator (or whitespace) is only accepted as a thousands/lakh grouping
    when it splits digits into valid groups; a lone run of digits is accepted
    ungrouped. Anything the pattern cannot match end-to-end is rejected by the
    caller rather than silently truncated (see issue #331)."""
    dec = re.escape(decimal)
    grp = rf"[{re.escape(separator)}\s]"
    # Either grouped digits (western 3s, indian 2/3s) or a plain run of digits.
    integer = rf"(?:\d{{1,3}}(?:{grp}\d{{2,3}})+|\d+)"
    number = rf"[+-]?\s?{integer}(?:{dec}\d+)?"
    # A unit is digit-free: any digit after the number may belong to a second,
    # glued-on number (a compact range, scientific notation, or a repeated
    # decimal/grouping char), which then fails the end-anchored match rather
    # than being mistaken for a unit (see issue #331).
    unit = r"[^\s\d]+"
    pattern = rf"^\s*(?P<number>{number})\s*(?P<unit>{unit})?\s*$"
    return re.compile(pattern, re.UNICODE)


class NumberType(PropertyType):
    """A numeric value, like the size of a piece of land, or the value of a
    contract. Since all property values in FtM are strings, this is also a
    string and there is no specified format (e.g. `1,000.00` vs. `1.000,00`).

    In the future we might want to enable annotations for format, units, or
    even to introduce a separate property type for monetary values."""

    DECIMAL = "."
    SEPARATOR = ","
    PRECISION = 2

    _FLOAT_FMT = "{:" + SEPARATOR + "." + str(PRECISION) + "f}"
    _INT_FMT = "{:" + SEPARATOR + "d}"

    name = "number"
    label = _("Number")
    plural = _("Numbers")
    matchable = False

    def node_id(self, value: str) -> None:
        return None

    def parse(
        self, value: str, decimal: str = DECIMAL, separator: str = SEPARATOR
    ) -> tuple[str | None, str | None]:
        """Parse a number into a numeric value and a unit. The numeric value is
        aligned with the decimal and separator settings. The unit is stripped of
        whitespace and returned as a string. If no unit is found, None is
        returned. If no number is found, None is returned for both values.

        Args:
            value (str): The string to parse.
            decimal (str): The character used as the decimal separator.
            separator (str): The character used to separate thousands, lakhs, or crores.

        Returns:
            A tuple of (number, unit), where number is a string and unit is a string or None.

        Returns (None, None) when the string is not a single, well-formed number
        with an optional unit. Ambiguous or multi-number inputs (e.g. ranges, or a
        European decimal comma under the default separator) are rejected rather
        than silently coerced into a structurally different value (see issue #331).
        """
        match = _number_pattern(decimal, separator).match(value.strip())
        if match is None:
            return None, None
        unit = match.group("unit")
        if unit is not None:
            unit = unit.strip()
            if len(unit) == 0:
                unit = None
        # TODO: We could have a lookup table for common units, e.g. kg, m, etc. to
        # convert them to a standard form.
        number = match.group("number").replace(separator, "")
        number = re.sub(r"\s+", "", number)
        if decimal != self.DECIMAL:
            number = number.replace(decimal, self.DECIMAL)
        if number == "":
            return None, None
        return number, unit

    def to_number(self, value: str) -> float | None:
        """Convert a number string to a float. The string is parsed and the unit is
        discarded if present.

        Args:
            value (str): The string to convert.

        Returns:
            Optional[float]: The parsed float value, or None if parsing fails.
        """
        try:
            number, _ = self.parse(value)
            if number is None:
                return None
            return float(number)
        except (AttributeError, ValueError, TypeError):
            return None

    def caption(self, value: str, format: str | None = None) -> str:
        """Return a caption for the number. This is used for display purposes.

        Args:
            value (str): The string to format.
            format (Optional[str]): An optional format string to use for formatting the number.

        Returns:
            str: The formatted number string, possibly with a unit.
        """
        number, unit = self.parse(value)
        if number is None:
            return value
        try:
            fnumber = float(number)
        except ValueError:
            return value
        if format is not None:
            number = format.format(fnumber)
        elif fnumber.is_integer():
            number = self._INT_FMT.format(int(fnumber))
        else:
            number = self._FLOAT_FMT.format(fnumber)
        if unit is not None:
            return f"{number} {unit}"
        return number
