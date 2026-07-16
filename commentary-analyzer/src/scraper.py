import requests
import os
import time
from bs4 import BeautifulSoup

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible)"}

def scrape_match(url, match_name):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"failed to fetch {url} — status {response.status_code}")
            return
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
        os.makedirs("data/raw", exist_ok=True)
        filepath = f"data/raw/{match_name}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"saved {len(text)} chars to {filepath}")
    except Exception as e:
        print(f"error scraping {url}: {e}")

if __name__ == "__main__":
    matches = [
        ("https://www.bbc.com/sport/football/articles/PUT_ARTICLE_URL_HERE", "match_name_here"),
    ]
    for url, name in matches:
        scrape_match(url, name)
        time.sleep(2)