from __future__ import annotations

from scrapling import StealthyFetcher, Selector

urls = [
    "https://www.olx.pt",
    "https://www.olx.pt/search",
    "https://www.olx.pt/search?q=RTX",
]

for url in urls:
    try:
        response = StealthyFetcher.fetch(url, solve_cloudflare=True, timeout=30000, wait=1500)
    except Exception as exc:
        print(f"FETCH ERROR: {url} -> {exc}")
        continue
    final_url = getattr(response, "url", url)
    status = getattr(response, "status_code", "?")
    length = len(response.text or "")
    print(f"{status} {final_url} len={length}")
    if length:
        print(response.text[:500])
        print("---")
