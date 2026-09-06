from __future__ import annotations

from scrapling import StealthyFetcher, Selector

response = StealthyFetcher.fetch("https://www.olx.pt", solve_cloudflare=True, timeout=30000, wait=1500)
html = response.text or ""
print(f"Homepage length: {len(html)}")
print(html[:3000])
