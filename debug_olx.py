import requests
from bs4 import BeautifulSoup

url = "https://www.olx.pt/search?q=RTX&page=1"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)}")

soup = BeautifulSoup(response.text, 'html.parser')
# Try to find listing cards with various selectors
selectors = [
    '[data-testid="listing-card"]',
    'article',
    '[data-cy="l-card"]',
    '.css-1d8gd2y',  # OLX often uses these CSS classes
    '[href*="/anuncio/"]',
    '[href*="/ad/"]'
]

for sel in selectors:
    elements = soup.select(sel)
    print(f"{sel}: {len(elements)} elements")
    if elements:
        print(f"  Sample: {elements[0].get_text(strip=True)[:200]}")
