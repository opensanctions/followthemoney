from typing import TYPE_CHECKING

from rigour.mime import DEFAULT, normalize_mimetype, parse_mimetype

from followthemoney.types.common import PropertyType
from followthemoney.util import defer as _

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


class MimeType(PropertyType):
    """A MIME media type are a specification of a content type on a network.
    Each MIME type is assigned by IANA and consists of two parts: the type
    and sub-type. Common examples are: `text/plain`, `application/json` and
    `application/pdf`.

    MIME type properties do not contain parameters as used in HTTP headers,
    like `charset=UTF-8`."""

    name = "mimetype"
    group = "mimetypes"
    label = _("MIME-Type")
    plural = _("MIME-Types")
    matchable = False

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        text = normalize_mimetype(text)
        if text != DEFAULT:
            return text
        return None

    def caption(self, value: str, format: str | None = None) -> str:
        return parse_mimetype(value).label or value
