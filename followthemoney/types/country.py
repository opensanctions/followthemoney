from typing import Callable, Optional, TYPE_CHECKING, Sequence
from babel.core import Locale
from rigour.territories import get_ftm_countries, lookup_territory
from rigour.territories import territories_intersect

from followthemoney.types.common import EnumType, EnumValues
from followthemoney.util import defer as _

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


class CountryType(EnumType):
    """Properties to define countries and territories. This is completely
    descriptive and needs to deal with data from many origins, so we support
    a number of unusual and controversial designations (e.g. the Soviet Union,
    Transnistria, Somaliland, Kosovo)."""

    name = "country"
    group = "countries"
    label = _("Country")
    plural = _("Countries")
    matchable = True
    max_length = 16

    def _locale_names(self, locale: Locale) -> EnumValues:
        return {t.code: t.name for t in get_ftm_countries()}

    def compare(self, left: str, right: str) -> float:
        overlap = territories_intersect([left], [right])
        return 1.0 if len(overlap) else 0.0

    def compare_sets(
        self,
        left: Sequence[str],
        right: Sequence[str],
        func: Callable[[Sequence[float]], float] = max,
    ) -> float:
        """Compare two sets of values and select the highest-scored result."""
        overlap = territories_intersect(left, right)
        return 1.0 if len(overlap) else 0.0

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: Optional[str] = None,
        proxy: Optional["EntityProxy"] = None,
    ) -> Optional[str]:
        """Determine a two-letter country code based on an input.

        The input may be a country code, a country name, etc.
        """
        territory = lookup_territory(text, fuzzy=fuzzy)
        if territory is not None:
            ftm_country = territory.ftm_country
            if ftm_country is not None:
                return ftm_country
        return None

    def country_hint(self, value: str) -> str:
        return value
