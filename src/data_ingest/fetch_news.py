import os
import re
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from src.llm.response_engine import refine_search_query


load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")


# ------------------------
# helpers
# ------------------------
def _clean_author(raw_author, source_name):
    if not raw_author or str(raw_author).lower() in ("nan", "none", "null", ""):
        return source_name or "News Desk"
    a = str(raw_author)
    a = re.sub(r"http\S+|www\.\S+", "", a)
    a = re.sub(r"^by\s+", "", a, flags=re.I)
    a = a.split(",")[0].strip()
        # allow Hindi / international characters
    a = re.sub(r"[^\w\s@\.]", "", a, flags=re.UNICODE).strip()

    # if email-like
    if "@" in a:
        name = a.split("@")[0].replace(".", " ").title()
        return name if len(name) >= 3 else (source_name or "News Desk")
    # drop common role words
    for w in ["contributor", "staff writer", "editor", "reporter", "tech desk"]:
        a = re.sub(w, "", a, flags=re.I).strip()
    return a if len(a) >= 2 else (source_name or "News Desk")


def _is_garbage_title(t):
    if not t:
        return True
    t = t.strip().lower()
    if re.search(r'\b\d+(\.\d+){1,3}\b', t):
        return True
    return len(t) < 4


def _is_relevant(text: str, topic: str) -> bool:
    if not text or not topic:
        return False
    text = text.lower()
    twords = [w for w in re.findall(r"\w+", topic.lower())]
    if not twords:
        return False
    score = sum(1 for w in twords if w in text)
    if score >= 1:
        return True
    # proximity check
    tokens = re.sub(r"[^a-z0-9\s]", " ", text).split()
    for i in range(len(tokens) - 1):
        if tokens[i] in twords:
            for j in range(i + 1, min(i + 7, len(tokens))):
                if tokens[j] in twords and tokens[j] != tokens[i]:
                    return True
    return False


def _format_time(dt: datetime) -> str:
    now = datetime.now(timezone.utc)
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt.astimezone(timezone.utc)
    hours = int(diff.total_seconds() // 3600)
    if hours < 24:
        return f"{hours} hrs ago"
    return dt.strftime("%Y-%m-%d")


def fetch_news(topic="news", max_articles=20):
    """
    Safe, stable news fetcher.
    - No refine_search_query for news (handled in intent)
    - No broken variants
    - No quotes or split-word garbage
    """
    try:
        print(f"📰 Fetching News for '{topic}'...")

        # 🔥 SAFETY: remove quotes that break NewsAPI
        topic = topic.replace('"', '').replace("'", "").strip()
        print(f"🔍 Cleaned topic for news: {topic}")

        today = datetime.now(timezone.utc)
        week_ago = today - timedelta(days=7)

        out = []

        # 🔥 VERY IMPORTANT: use ONLY ONE variant
        topic_variants = [topic]

        # === NEWSAPI FIRST ===
        if NEWS_API_KEY:
            url = "https://newsapi.org/v2/everything"

            for variant in topic_variants:
                params = {
                    "q": variant,
                    "searchIn": "title,description",
                    "language": "en",
                    "sortBy": "relevancy",
                    "pageSize": max_articles,
                    "from": week_ago.strftime("%Y-%m-%d"),
                    "apiKey": NEWS_API_KEY,
                }

                try:
                    r = requests.get(url, params=params, timeout=10)
                    print(f"🛰️ NewsAPI HTTP {r.status_code} for '{variant}'")
                    data = r.json()
                except Exception as e:
                    print(f"❌ NewsAPI request failed for '{variant}': {e}")
                    continue

                # skip invalid responses
                if r.status_code != 200 or data.get("status") != "ok":
                    continue

                for art in data.get("articles", []):
                    title = art.get("title") or ""
                    desc = art.get("description") or ""
                    author = art.get("author") or ""
                    combined = f"{title} {desc} {author}"

                    # Less strict for well-known sources
                    trusted = art.get("source", {}).get("name", "").lower()
                    trust_list = ["times of india", "indian express", "bbc", "reuters", "ndtv", "hindustan times"]

                    if _is_garbage_title(title):
                        continue

                    if not _is_relevant(combined, topic):
                        if not any(t in trusted for t in trust_list):
                            continue


                    published = art.get("publishedAt")
                    try:
                        published_dt = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else week_ago
                    except Exception:
                        published_dt = week_ago

                    # skip too old
                    if published_dt < week_ago:
                        continue

                    out.append({
                        "source_type": "news",
                        "source": art.get("source", {}).get("name", "Unknown"),
                        "title": title.strip(),
                        "description": desc.strip() if desc else "",
                        "url": art.get("url"),
                        "publishedAt": published_dt,
                        "published": _format_time(published_dt),
                        "author": _clean_author(author, art.get("source", {}).get("name")),
                    })

                if len(out) >= max_articles:
                    break

        # === GNEWS FALLBACK ===
        if not out and GNEWS_API_KEY:
            gurl = "https://gnews.io/api/v4/search"
            for variant in topic_variants:
                params = {
                    "q": variant,
                    "lang": "en",
                    "max": max_articles,
                    "token": GNEWS_API_KEY
                }

                try:
                    r = requests.get(gurl, params=params, timeout=10)
                    data = r.json()
                except Exception as e:
                    print(f"❌ GNews request failed for '{variant}': {e}")
                    continue

                for art in data.get("articles", []):
                    title = art.get("title") or ""
                    desc = art.get("description") or ""

                    if _is_garbage_title(title) or not _is_relevant(f"{title} {desc}", topic):
                        continue

                    pub = art.get("publishedAt")
                    try:
                        published_dt = datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else week_ago
                    except Exception:
                        published_dt = week_ago

                    out.append({
                        "source_type": "news",
                        "source": art.get("source", {}).get("name", "Unknown"),
                        "title": title.strip(),
                        "description": desc.strip() if desc else "",
                        "url": art.get("url"),
                        "publishedAt": published_dt,
                        "published": _format_time(published_dt),
                        "author": _clean_author(art.get("author"), art.get("source", {}).get("name")),
                    })

                if len(out) >= max_articles:
                    break

        print(f"✅ News fetched: {len(out)} items")
        return out

    except Exception as e:
        print(f"❌ fetch_news error: {e}")
        return []
