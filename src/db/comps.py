from __future__ import annotations

import csv
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iter

import requests
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.db.models import Comp
from src.db.session import SessionLocal


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


def _to_float(value: str) -> float:
    cleaned = re.sub(r"[^0-9,\.]", "", value or "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


@dataclass
class CompRecord:
    model: str
    price: float
    currency: str = "EUR"
    source: str | None = None
    url: str | None = None


def add_comp(db: Session, record: CompRecord) -> Comp:
    comp = Comp(
        id=str(uuid.uuid4()),
        model=record.model,
        price=record.price,
        currency=record.currency,
        source=record.source,
        url=record.url,
    )
    db.add(comp)
    db.flush()
    return comp


def add_comps(db: Session, records: Iterable[CompRecord]) -> list[Comp]:
    out = []
    for record in records:
        out.append(add_comp(db, record))
    db.commit()
    return out


def import_csv(path: Path, source_label: str | None = None) -> list[CompRecord]:
    records: list[CompRecord] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            model = _normalize_model(row.get("title") or row.get("model") or "")
            if not model:
                continue
            price = _to_float(row.get("price", "0"))
            if price <= 0:
                continue
            records.append(
                CompRecord(
                    model=model,
                    price=price,
                    currency=(row.get("currency") or "EUR").upper(),
                    source=row.get("source") or source_label,
                    url=row.get("url") or None,
                )
            )
    return records


def seed_from_olx_snapshot(queries: Iterable[str], max_pages: int = 3) -> list[CompRecord]:
    from src.scrapers.olx import OLXScraper

    scraper = OLXScraper(settings.olx_base_url, max_pages=max_pages)
    records: list[CompRecord] = []
    for listing in scraper.fetch_pages(queries):
        model = _normalize_model(listing.title)
        if not model:
            continue
        records.append(
            CompRecord(
                model=model,
                price=listing.price,
                currency=listing.currency,
                source="olx",
                url=listing.url,
            )
        )
    return records


def ingest_olx_snapshot() -> int:
    db = SessionLocal()
    try:
        records = seed_from_olx_snapshot(["RTX", "RX", "placa gráfica", "GPU"], max_pages=settings.scrape_max_pages)
        if not records:
            return 0
        add_comps(db, records)
        return len(records)
    finally:
        db.close()


if __name__ == "__main__":
    count = ingest_olx_snapshot()
    print(f"Seeded {count} comps from OLX snapshot.")
