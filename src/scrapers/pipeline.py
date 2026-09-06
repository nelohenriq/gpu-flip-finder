from __future__ import annotations

from typing import Iterable

from src.scrapers.olx import OLXScraper


def run_pipeline(queries: Iterable[str], max_pages: int = 5):
    scraper = OLXScraper("https://www.olx.pt", max_pages=max_pages)
    yield from scraper.fetch_pages(queries)
