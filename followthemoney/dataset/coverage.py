from typing import Literal, TypeAlias
from pydantic import BaseModel

from followthemoney.dataset.util import CountryCode, PartialDate


# Derived from Aleph
FREQUENCY_TYPE: TypeAlias = Literal[
    "unknown",
    "never",
    "hourly",
    "daily",
    "weekly",
    "monthly",
    "annually",
]


class DataCoverage(BaseModel):
    """Details on the temporal and geographic scope of a dataset."""

    start: PartialDate | None = None
    end: PartialDate | None = None
    countries: list[CountryCode] = []
    frequency: FREQUENCY_TYPE = "unknown"
    schedule: str | None = None

    def __repr__(self) -> str:
        return f"<DataCoverage({self.start!r}, {self.end!r}, {self.countries!r})>"
