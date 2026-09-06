import requests

url = "https://www.olx.pt/search?q=RTX&page=1"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
}
response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
print(f"Content length: {len(response.text)}")
print("--- HEAD ---")
print(response.text[:2000])
print("--- TAIL ---")
print(response.text[-1000:])
