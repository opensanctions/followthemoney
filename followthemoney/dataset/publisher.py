
from pydantic import BaseModel, computed_field

from followthemoney.dataset.util import CountryCode, Url
from followthemoney.types import registry


class DataPublisher(BaseModel):
    """Publisher information, eg. the government authority."""

    name: str
    url: Url | None = None
    name_en: str | None = None
    acronym: str | None = None
    description: str | None = None
    country: CountryCode | None = None
    official: bool | None = False
    logo_url: Url | None = None

    # Re: the type: ignore, see https://github.com/python/mypy/issues/1362 and https://docs.pydantic.dev/2.0/usage/computed_fields/
    @computed_field # type: ignore[prop-decorator]
    @property
    def country_label(self) -> str | None:
        if self.country is None:
            return None
        return registry.country.caption(self.country)
