"""
Fetch news articles from NewsAPI and save raw JSON to data/raw/news_<timestamp>.json
Now compatible with Streamlit user input (via fetch_and_save_news function)
"""

import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

# 1️⃣ Load your .env file
load_dotenv()
API_KEY = os.getenv("NEWSAPI_KEY")

if not API_KEY:
    raise ValueError("NEWSAPI_KEY not found! Add it to the .env file.")

# 2️⃣ Config paths
BASE_URL = "https://newsapi.org/v2/everything"
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# 3️⃣ Setup logging
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOGS_DIR / "fetch_news.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_news(query="AI", pages=1, page_size=50):
    """
    Fetch news articles about a topic and save them to data/raw/
    Returns: Path of saved JSON file
    """
    headers = {"Authorization": API_KEY}
    all_articles = []
    logging.info(f"Starting fetch for query: {query}")

    for page in range(1, pages + 1):
        params = {
            "q": query,
            "language": "en",
            "pageSize": page_size,
            "page": page
        }

        response = requests.get(BASE_URL, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            all_articles.extend(articles)
            logging.info(f"Fetched {len(articles)} articles on page {page}")
            time.sleep(1)
        else:
            logging.warning(f"Error {response.status_code}: {response.text}")
            break

    # 4️⃣ Save to JSON
    filename = RAW_DIR / f"news_{query}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"articles": all_articles}, f, ensure_ascii=False, indent=2)

    logging.info(f"Saved {len(all_articles)} articles → {filename}")
    print(f"Saved {len(all_articles)} articles to {filename}")

    return filename


def fetch_and_save_news(query=None):
    """
    Wrapper for Streamlit integration.
    If query is None, it will ask user input (for local test).
    """
    if query is None:
        query = input("Enter a topic: ").strip() or "AI"
    print(f"🔍 Fetching news for: {query}")
    return fetch_news(query)


# ✅ Local run
if __name__ == "__main__":
    fetch_and_save_news()
