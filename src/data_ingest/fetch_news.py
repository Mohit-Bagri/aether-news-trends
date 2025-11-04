import os
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_news(topic: str, page_size: int = 50):
    """
    Fetch top news articles for a given topic using NewsAPI.
    Saves data as CSV and returns file path.
    """
    if not NEWS_API_KEY:
        raise ValueError("❌ Missing NEWSAPI_KEY in .env")

    print(f"📰 Fetching fresh news for topic: {topic} ...")

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": topic,
        "language": "en",
        "pageSize": page_size,
        "sortBy": "relevancy",
        "apiKey": NEWS_API_KEY,
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data.get("status") != "ok":
        print(f"⚠️ Error fetching news: {data.get('message')}")
        return None

    articles = data.get("articles", [])
    if not articles:
        print(f"⚠️ No news found for {topic}")
        return None

    records = []
    for a in articles:
        records.append({
            "title": a.get("title", ""),
            "text": a.get("description", ""),
            "url": a.get("url", ""),
            "publishedAt": a.get("publishedAt", ""),
            "source": a.get("source", {}).get("name", ""),
            "source_type": "news"
        })

    df = pd.DataFrame(records)

    # Save file
    output_path = Path(f"data/raw/cleaned_news_{topic.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"✅ Cleaned news data saved to: {output_path} ({len(df)} rows)")
    return output_path


# Debug run
if __name__ == "__main__":
    fetch_news("AI News")
