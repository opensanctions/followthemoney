from typing import TYPE_CHECKING, ClassVar

from babel.core import Locale

from followthemoney.types.common import EnumType, EnumValues
from followthemoney.util import defer as _
from followthemoney.util import gettext

if TYPE_CHECKING:
    from followthemoney.proxy import EntityProxy


class GenderType(EnumType):
    """A human gender. This is not meant to be a comprehensive model of
    the social realities of gender but a way to capture data from (mostly)
    government databases and represent it in a way that can be used by
    structured tools. I'm not sure this justifies the simplification."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

    LOOKUP: ClassVar[dict[str, str]] = {
        "m": MALE,
        "man": MALE,
        "masculin": MALE,
        "männlich": MALE,
        "мужской": MALE,
        "男": MALE,
        "f": FEMALE,
        "woman": FEMALE,
        "féminin": FEMALE,
        "weiblich": FEMALE,
        "женский": FEMALE,
        "女": FEMALE,
        "o": OTHER,
        "d": OTHER,
        "divers": OTHER,
    }

    name = "gender"
    group = "genders"
    label = _("Gender")
    plural = _("Genders")
    matchable = False
    max_length = 16

    def _locale_names(self, locale: Locale) -> EnumValues:
        return {
            self.MALE: gettext("male"),
            self.FEMALE: gettext("female"),
            self.OTHER: gettext("other"),
        }

    def clean_text(
        self,
        text: str,
        fuzzy: bool = False,
        format: str | None = None,
        proxy: "EntityProxy | None" = None,
    ) -> str | None:
        code = text.lower().strip()
        code = self.LOOKUP.get(code, code)
        if code not in self.codes:
            return None
        return code
