from __future__ import annotations

import re
from dataclasses import dataclass

from src.scrapers.olx import Listing


@dataclass
class ListingScore:
    listing: Listing
    relevance: float
    risk: float


def _keywords() -> tuple[list[str], list[str]]:
    include = ["rtx", "rx", "gpu", "placa gráfica", "radeon", "geforce", "miner", "usado", "testado", "garantia"]
    exclude = ["notebook", "laptop", "motherboard", "cpu", "sem placa", "peças", "avariado", "para peças"]
    return [s.lower() for s in include], [s.lower() for s in exclude]


def score_listing(listing: Listing) -> ListingScore:
    include, exclude = _keywords()
    text = f"{listing.title} {listing.condition or ''}".lower()
    relevance = sum(1.0 for word in include if word in text)
    risk = sum(1.0 for word in exclude if word in text)
    if listing.price <= 0:
        risk += 2
    return ListingScore(listing=listing, relevance=relevance, risk=risk)
