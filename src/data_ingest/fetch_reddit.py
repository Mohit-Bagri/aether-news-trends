import requests
import re
from datetime import datetime, timedelta, timezone
from src.llm.response_engine import refine_search_query


def _is_relevant(text: str, topic: str):
    """Smart semantic relevance checker (v2.1)"""
    text = (text or "").lower()
    topic = topic.lower()
    topic_words = [w for w in re.findall(r"\w+", topic)]

    if not text or not topic_words:
        return False

    score = sum(1 for w in topic_words if w in text)
    similar = (
        topic in text
        or re.search(rf"\b{re.escape(topic[:-1])}\w*\b", text)
        or any(w in text for w in topic_words)
    )

    window_text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = window_text.split()
    proximity_hits = 0
    for i in range(len(tokens) - 1):
        if tokens[i] in topic_words:
            for j in range(i + 1, min(i + 7, len(tokens))):
                if tokens[j] in topic_words and tokens[j] != tokens[i]:
                    proximity_hits += 1
                    break

    return (score >= 2 or proximity_hits >= 1 or similar) if len(topic_words) >= 2 else (score >= 1 or similar)


def fetch_reddit_posts(topic="news", limit=30):
    """Fetch Reddit posts as list[dict] compatible with Aether’s pipeline."""
    print(f"🧵 Reddit: Fetching posts for '{topic}'...")
    topic = refine_search_query(topic)
    print(f"🔍 Refined Reddit topic: {topic}")

    topic_variants = list(dict.fromkeys([
        topic.strip(),
        topic.split()[0] if " " in topic else topic,
        topic.split()[-1] if " " in topic else topic,
        re.sub(r"operation\s+", "", topic, flags=re.I),
    ]))

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    posts = []

    for variant in topic_variants:
        url = f"https://www.reddit.com/search.json?q={variant}&sort=top&t=week&limit={limit}"
        headers = {"User-agent": "AetherBot/3.1"}

        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 429:
                print("⛔ Reddit rate limit — skipping variant temporarily.")
                continue
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"⚠️ Reddit fetch failed for '{variant}': {e}")
            continue

        for post in data.get("data", {}).get("children", []):
            p = post.get("data", {})
            title = p.get("title", "").strip()
            body = (p.get("selftext") or "").strip()
            sub = p.get("subreddit") or ""

            if len(title.split()) < 3:
                continue

            combined = f"{title} {body} {sub}"
            if not _is_relevant(combined, topic):
                continue

            created = datetime.fromtimestamp(p.get("created_utc", 0), tz=timezone.utc)
            if created < week_ago:
                continue

            upvotes = int(p.get("score", 0))
            comments = int(p.get("num_comments", 0))
            hours = max(1, int((now - created).total_seconds() // 3600))
            published_str = f"{hours}h ago" if hours < 24 else created.strftime("%Y-%m-%d")

            posts.append({
                "source_type": "reddit",
                "title": title,
                "url": f"https://reddit.com{p.get('permalink','')}",
                "subreddit": sub,
                "upvotes": upvotes,
                "comments": comments,
                "published": published_str
            })

        if len(posts) >= 10:
            break

    if not posts:
        print(f"⚠️ Reddit: No relevant posts for '{topic}'")
        return []

    # Remove duplicates by title
    seen = set()
    unique_posts = []
    for p in posts:
        if p["title"].lower() not in seen:
            seen.add(p["title"].lower())
            unique_posts.append(p)

    print(f"✅ Reddit: {len(unique_posts)} relevant posts found (top: {unique_posts[0]['title'][:60]}...)")
    return unique_posts
