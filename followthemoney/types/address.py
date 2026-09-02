import re
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from normality import slugify_text, squash_spaces
from rigour.addresses import address_fingerprint, compare_address, compare_address_many

from followthemoney.types.common import PropertyType
from followthemoney.util import dampen
from followthemoney.util import defer as _

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


class AddressType(PropertyType):
    """A geographic address used to describe a location of a residence or post
    box. There is no specified order for the sub-parts of an address (e.g. street,
    city, postal code), and we should consider introducing an Address schema type
    to retain fidelity in cases where address parts are specified."""

    LINE_BREAKS = re.compile(r"(\r\n|\n|<BR/>|<BR>|\t|ESQ\.,|ESQ,|;)")
    COMMATA = re.compile(r"(,\s?[,\.])")
    name = "address"
    group = "addresses"
    label = _("Address")
    plural = _("Addresses")
    matchable = True
    pivot = True

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        """Basic clean-up."""
        address = self.LINE_BREAKS.sub(", ", text)
        address = self.COMMATA.sub(", ", address)
        collapsed = squash_spaces(address)
        if len(collapsed) < 1:
            return None
        return collapsed

    def compare_sets(
        self,
        left: Sequence[str],
        right: Sequence[str],
        func: Callable[[Sequence[float]], float] = max,
    ) -> float:
        """Compare two sets of addresses. This can be done entirely in native code if
        the comparison function is max, otherwise we defer to the superclass."""
        if func is not max:
            return super().compare_sets(left, right, func)
        return compare_address_many(list(left), list(right))

    def compare(self, left: str, right: str) -> float:
        return compare_address(left, right)

    def _specificity(self, value: str) -> float:
        return dampen(10, 60, value)

    def node_id(self, value: str) -> str | None:
        normalized = address_fingerprint(value)
        if normalized is None:
            return None
        slug = slugify_text(normalized)
        if slug is None:
            return None
        return f"addr:{slug}"
