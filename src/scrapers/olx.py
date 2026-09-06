from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import requests
from scrapling.fetchers import RequestsFetcher
from scrapling.parser import Selector


@dataclass
class Listing:
    source: str
    external_id: str
    title: str
    url: str
    price: float
    currency: str
    condition: str | None = None
    location: str | None = None
    seller: str | None = None


class OLXScraper:
    def __init__(self, base_url: str, max_pages: int = 5, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def _search_url(self, query: str, page: int) -> str:
        return f"{self.base_url}/search?q={requests.utils.quote(query)}&page={page}"

    def _to_float(self, value: str) -> float:
        cleaned = re.sub(r"[^0-9,\.]", "", value or "").replace(",", ".")
        if not cleaned:
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def fetch_pages(self, queries: Iterable[str]) -> Iterable[Listing]:
        for query in queries:
            for page in range(1, self.max_pages + 1):
                url = self._search_url(query, page)
                try:
                    response = self.session.get(url, timeout=self.timeout)
                except requests.RequestException:
                    break
                if response.status_code != 200:
                    break
                yield from self._parse_listings(response.text)

    def _parse_listings(self, html: str) -> Iterable[Listing]:
        try:
            selector = Selector(text=html, proxy=None)
        except Exception:
            return

        cards = selector.css('[data-testid="listing-card"], article, [data-cy="l-card"]')
        if not cards:
            return

        seen = set()
        for card in cards:
            title = card.css("h6, [data-testid='ad-title'], .title").get_text(" ", strip=True)
            href = card.css("a::attr(href)").get()
            price_raw = card.css("[data-testid='ad-price'], .price").get_text(" ", strip=True)
            if not title or not href or not price_raw:
                continue

            url = href if href.startswith("http") else f"{self.base_url}{href}"
            external_id = re.search(r"/(\d{6,})(?:[?#]|$)", url)
            external_id = external_id.group(1) if external_id else url
            if external_id in seen:
                continue
            seen.add(external_id)

            price = self._to_float(price_raw)
            if price <= 0:
                continue

            location = card.css(".location, [data-testid='location-name']").get_text(" ", strip=True) or None
            condition = card.css(".condition, [data-testid='ad-status']").get_text(" ", strip=True) or None

            yield Listing(
                source="olx",
                external_id=external_id,
                title=title,
                url=url,
                price=price,
                currency="EUR",
                condition=condition,
                location=location,
            )
