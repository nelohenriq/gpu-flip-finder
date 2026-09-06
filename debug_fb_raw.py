from __future__ import annotations

from scrapling import DynamicFetcher

response = DynamicFetcher.fetch(
    "https://www.facebook.com/marketplace/porto/search?query=RTX",
    wait=3000,
    timeout=45000,
)
html = response.text or ""
print(f"Length: {len(html)}")
print(html[:4000])
print("---")
print("PORTUGAL" in html)
print("Porto" in html)
print("San Francisco" in html)
