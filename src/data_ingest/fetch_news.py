import os
import requests
import pandas as pd
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")

def clean_author(raw_author, source_name):
    if not raw_author or str(raw_author).lower() in ["nan", "none", "null", ""]:
        return source_name or "News Desk"

    author = str(raw_author)
    author = re.sub(r"http\S+|www\.\S+", "", author)
    author = re.sub(r"^by\s+", "", author, flags=re.IGNORECASE)
    author = author.split(",")[0].strip()

    rm_words = ["contributor", "staff writer", "editor", "reporter", "tech desk"]
    for w in rm_words:
        author = re.sub(w, "", author, flags=re.IGNORECASE).strip()

    if "@" in author:
        name = author.split("@")[0].replace(".", " ").title()
        return name if len(name) >= 3 else (source_name or "News Desk")

    author = re.sub(r"[^a-zA-Z\s]", "", author).strip()

    if len(author) < 2 or len(author.split()) > 4:
        return source_name or "News Desk"

    return author


def is_garbage_title(title: str):
    if not title:
        return True
    title = title.strip().lower()
    if re.search(r'\b\d+(\.\d+){1,3}\b', title):
        return True
    if len(title) < 4:
        return True
    return False


def fetch_news(topic="news", max_articles=20):
    print(f"📰 Fetching News for '{topic}'...")
    today = datetime.now(timezone.utc)
    week_ago = today - timedelta(days=7)

    all_articles = []

    # ---------- NEWS API ----------
    try:
        print("🌐 Source: NewsAPI")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": topic,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max_articles,
            "from": week_ago.strftime("%Y-%m-%d"),
            "apiKey": NEWS_API_KEY
        }

        resp = requests.get(url, params=params, timeout=10)
        print(f"🛰️ NewsAPI HTTP {resp.status_code}")
        data = resp.json()

        if data.get("status") != "ok":
            print(f"⚠️ NewsAPI error: {data.get('code', 'unknown')} — {data.get('message', 'No details')}")
        else:
            for art in data.get("articles", []):
                title = art.get("title") or ""
                if is_garbage_title(title):
                    continue
                all_articles.append({
                    "source": art.get("source", {}).get("name", "Unknown"),
                    "title": title,
                    "description": art.get("description"),
                    "url": art.get("url"),
                    "publishedAt": art.get("publishedAt"),
                    "author": clean_author(art.get("author"), art.get("source", {}).get("name"))
                })
            print(f"✅ NewsAPI fetched {len(all_articles)} articles")

    except Exception as e:
        print(f"❌ NewsAPI request failed: {e}")

    # ---------- FALLBACK: GNEWS ----------
    if not all_articles:
        print("🔁 Using GNews fallback...")
        try:
            gnews_url = "https://gnews.io/api/v4/search"
            params = {
                "q": topic,
                "lang": "en",
                "max": max_articles,
                "token": GNEWS_API_KEY
            }
            resp = requests.get(gnews_url, params=params, timeout=10)
            print(f"🛰️ GNews HTTP {resp.status_code}")
            data = resp.json()

            if data.get("errors") or not data.get("articles"):
                print(f"⚠️ GNews error or empty response: {data}")
            else:
                for art in data.get("articles", []):
                    title = art.get("title") or ""
                    if is_garbage_title(title):
                        continue
                    source = art.get("source", {}).get("name", "Unknown")
                    all_articles.append({
                        "source": source,
                        "title": title,
                        "description": art.get("description"),
                        "url": art.get("url"),
                        "publishedAt": art.get("publishedAt"),
                        "author": clean_author(source, source)
                    })
                print(f"✅ GNews fetched {len(all_articles)} articles")

        except Exception as e2:
            print(f"❌ GNews request failed: {e2}")

    # ---------- FINALIZE ----------
    if not all_articles:
        print(f"⚠️ No news articles found for '{topic}'. Possible causes:")
        print("   • Typo in query (try a common keyword)")
        print("   • NewsAPI daily limit exceeded")
        print("   • Invalid or expired GNews token")
        return pd.DataFrame()

    df = pd.DataFrame(all_articles)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce", utc=True)
    df = df.dropna(subset=["publishedAt"])
    df = df[df["publishedAt"] >= week_ago]
    df = df.sort_values(by="publishedAt", ascending=False)

    print(f"✅ Final News DataFrame with {len(df)} rows")
    return df
