"""Validated buyer records and provenance."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    collected_on: str
    authorization: str
    record_type: str


@dataclass
class Buyer:
    company_name: str
    normalized_name: str
    country: str
    materials: set[str] = field(default_factory=set)
    sources: list[Source] = field(default_factory=list)
