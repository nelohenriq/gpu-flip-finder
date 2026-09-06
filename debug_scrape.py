from __future__ import annotations

import re
from typing import Iterable

from scrapling import DynamicFetcher, Selector


class Listing:
    def __init__(self, source, external_id, title, url, price, currency="EUR", condition=None, location=None, seller=None):
        self.source = source
        self.external_id = external_id
        self.title = title
        self.url = url
        self.price = price
        self.currency = currency
        self.condition = condition
        self.location = location
        self.seller = seller


class OLXScraper:
    def __init__(self, base_url="https://www.olx.pt", max_pages=5, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.timeout = timeout * 1000

    def _to_float(self, value):
        cleaned = re.sub(r"[^0-9,\.]", "", value or "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def fetch_pages(self, queries: Iterable[str]):
        for query in queries:
            for page in range(1, self.max_pages + 1):
                url = f"{self.base_url}/search?q={query.replace(' ', '+')}&page={page}"
                try:
                    response = DynamicFetcher.fetch(
                        url,
                        wait=2000,
                        timeout=self.timeout,
                    )
                except Exception as exc:
                    print(f"Fetch error for {url}: {exc}")
                    break
                if not response or not response.text:
                    break
                yield from self._parse_listings(response.text, query)

    def _parse_listings(self, html, query):
        try:
            selector = Selector(text=html, proxy=None)
        except Exception:
            return []

        cards = selector.css('[data-testid="listing-card"], article, [data-cy="l-card"]')
        print(f"Parsed {len(cards)} cards for query={query}")
        if not cards:
            return []

        seen = set()
        results = []
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

            results.append(Listing(
                source="olx",
                external_id=external_id,
                title=title,
                url=url,
                price=price,
                currency="EUR",
                condition=condition,
                location=location,
            ))
        return results


if __name__ == "__main__":
    scraper = OLXScraper("https://www.olx.pt", max_pages=1)
    results = list(scraper.fetch_pages(["RTX", "RX", "placa gráfica", "GPU"]))
    print(f"Found {len(results)} listings")
    for r in results[:10]:
        print(r.title, r.price, r.url)
