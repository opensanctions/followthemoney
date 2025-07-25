from typing import Optional
from pydantic import BaseModel, field_validator, computed_field

from followthemoney.dataset.util import Url, DateTimeISO
from followthemoney.types import registry


class DataResource(BaseModel):
    """A downloadable resource that is part of a dataset."""

    name: str
    url: Optional[Url] = None
    checksum: Optional[str] = None
    timestamp: Optional[DateTimeISO] = None
    mime_type: Optional[str] = None
    title: Optional[str] = None
    size: Optional[int] = None

    @field_validator("mime_type", mode="after")
    @classmethod
    def ensure_mime_type(cls, value: str) -> Optional[str]:
        cleaned = registry.mimetype.clean_text(value)
        if cleaned is None:
            raise ValueError(f"Invalid MIME type: {value!r}")
        return cleaned

    # Re: the type: ignore, see https://github.com/python/mypy/issues/1362 and https://docs.pydantic.dev/2.0/usage/computed_fields/
    @computed_field # type: ignore[prop-decorator]
    @property
    def mime_type_label(self) -> Optional[str]:
        if self.mime_type is None:
            return None
        return registry.mimetype.caption(self.mime_type)
