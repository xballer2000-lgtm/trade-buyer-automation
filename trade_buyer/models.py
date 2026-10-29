"""Validated buyer records and provenance."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    collected_on: str
    authorization: str
    record_type: str
    verified_on: str = ""
    products_purchased: str = ""
    business_email: str = ""
    website: str = ""
    buyer_evidence: str = ""
    record_date: str = ""
    terms_url: str = ""
    permission_basis: str = ""
    source_kind: str = ""
    verification_status: str = "unconfirmed_lead"


@dataclass
class Buyer:
    company_name: str
    normalized_name: str
    country: str
    materials: set[str] = field(default_factory=set)
    sources: list[Source] = field(default_factory=list)
