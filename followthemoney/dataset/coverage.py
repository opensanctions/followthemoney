from typing import List, Literal, Optional, TypeAlias
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

    start: Optional[PartialDate] = None
    end: Optional[PartialDate] = None
    countries: List[CountryCode] = []
    frequency: FREQUENCY_TYPE = "unknown"
    schedule: Optional[str] = None

    def __repr__(self) -> str:
        return f"<DataCoverage({self.start!r}, {self.end!r}, {self.countries!r})>"
