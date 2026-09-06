from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin

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


class FBMarketplaceScraper:
    def __init__(self, base_url="https://www.facebook.com/marketplace", max_pages=2, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.max_pages = max_pages
        self.timeout = timeout * 1000

    def _to_float(self, value):
        cleaned = re.sub(r"[^0-9,\.]", "", value or "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _candidate_urls(self, query, location="porto", category=None):
        q = query.replace(" ", "%20")
        cat = f"/category/{category}" if category else ""
        return [
            f"{self.base_url}/{location}/search?query={q}{cat}",
            f"{self.base_url}/search?query={q}{cat}",
        ]

    def fetch_pages(self, queries: Iterable[str]):
        for query in queries:
            urls = self._candidate_urls(query)
            html = None
            used_url = None
            for url in urls:
                try:
                    response = DynamicFetcher.fetch(
                        url,
                        wait=3000,
                        timeout=self.timeout,
                    )
                except Exception as exc:
                    print(f"Fetch error for {url}: {exc}")
                    continue
                if not response or not response.text:
                    continue
                html = response.text
                used_url = getattr(response, "url", url)
                break
            if not html:
                continue
            yield from self._parse_listings(html, query, used_url)

    def _parse_listings(self, html, query, base_url):
        try:
            selector = Selector(text=html, proxy=None)
        except Exception:
            return []

        cards = selector.css('[data-testid="marketplace_search_item_card"], [data-testid="marketplace_item"], article')
        print(f"Parsed {len(cards)} cards for query={query} from {base_url}")
        if not cards:
            return []

        seen = set()
        results = []
        for card in cards:
            title = card.css("[data-testid='marketplace_item_title'], h3, a span").get_text(" ", strip=True)
            href = card.css("a::attr(href)").get()
            price_raw = card.css("[data-testid='marketplace_item_price'], .price").get_text(" ", strip=True)
            if not title or not href or not price_raw:
                continue

            url = href if href.startswith("http") else urljoin(base_url or self.base_url, href)
            external_id = re.search(r"/(\d{6,})(?:[?#]|$)", url)
            external_id = external_id.group(1) if external_id else url
            if external_id in seen:
                continue
            seen.add(external_id)

            price = self._to_float(price_raw)
            if price <= 0:
                continue

            results.append(Listing(
                source="facebook_marketplace",
                external_id=external_id,
                title=title,
                url=url,
                price=price,
                currency="EUR",
            ))
        return results


if __name__ == "__main__":
    scraper = FBMarketplaceScraper(max_pages=1)
    results = list(scraper.fetch_pages(["RTX", "RX", "placa gráfica", "GPU"]))
    print(f"Found {len(results)} listings")
    for r in results[:10]:
        print(r.title, r.price, r.url)
