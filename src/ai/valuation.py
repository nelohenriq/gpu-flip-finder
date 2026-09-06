from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import median

from sqlalchemy.orm import Session

from src.db.models import Comp


@dataclass
class ValuationResult:
    model: str
    estimated_value: float
    confidence: str
    comps_used: int


_MODEL_HINTS = [
    r"rtx\s*30\d{2}",
    r"rtx\s*40\d{2}",
    r"rx\s*5\d{3}",
    r"rx\s*6\d{3}",
    r"rx\s*7\d{3}",
    r"gtx\s*10\d{2}",
    r"gtx\s*16\d{2}",
]


def _normalize_model(text: str) -> str | None:
    value = text.lower()
    for pattern in _MODEL_HINTS:
        match = re.search(pattern, value)
        if match:
            return match.group(0).replace(" ", "").upper()
    return None


def _median_for_model(db: Session, model: str) -> tuple[float | None, int]:
    prices = [row[0] for row in db.query(Comp.price).filter(Comp.model == model).all()]
    if not prices:
        return None, 0
    return float(median(prices)), len(prices)


def score_listing(db: Session, title: str, price: float) -> ValuationResult:
    model = _normalize_model(title) or "UNKNOWN"
    median_price, comps_used = _median_for_model(db, model)

    if median_price is None or median_price <= 0:
        estimated_value = price * 1.15
        confidence = "low"
    else:
        estimated_value = median_price
        confidence = "medium" if comps_used < 5 else "high"

    return ValuationResult(
        model=model,
        estimated_value=round(estimated_value, 2),
        confidence=confidence,
        comps_used=comps_used,
    )


def margin(price: float, estimated_value: float) -> float:
    if estimated_value <= 0:
        return -1.0
    return (estimated_value - price) / price
