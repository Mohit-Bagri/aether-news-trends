import requests, pandas as pd, re
from datetime import datetime, timedelta, timezone

def fetch_reddit_posts(topic="news", limit=30):
    print(f"🧵 Reddit: Fetching posts for '{topic}'...")

    url = f"https://www.reddit.com/search.json?q={topic}&sort=top&t=week&limit={limit}"
    headers = {"User-agent": "AetherBot/2.2"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 429:
            print("⛔ Reddit rate limit")
            return pd.DataFrame()
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"❌ Reddit failed: {e}")
        return pd.DataFrame()

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    posts = []

    for post in data.get("data", {}).get("children", []):
        p = post.get("data", {})
        title = p.get("title", "").strip()
        if not title: continue
        if len(title.split()) < 3: continue  # remove memes

        created = datetime.fromtimestamp(p.get("created_utc", 0), tz=timezone.utc)
        if created < week_ago: continue

        upvotes = int(p.get("score", 0))
        hours = max(1, int((now - created).total_seconds() // 3600))
        freshness = max(1, 168 - hours)

        score = upvotes*0.9 + freshness*0.1

        posts.append({
            "title": title,
            "url": f"https://reddit.com{p.get('permalink','')}",
            "subreddit": p.get("subreddit") or "unknown",
            "upvotes": upvotes,
            "publishedAt": created,
            "hours_ago": hours,
            "score": score
        })

    if not posts:
        print("⚠️ Reddit: no posts")
        return pd.DataFrame()

    df = pd.DataFrame(posts).sort_values(by="score", ascending=False)
    print(f"✅ Reddit: {len(df)} posts")
    return df[["title","url","subreddit","upvotes","publishedAt","hours_ago"]]
