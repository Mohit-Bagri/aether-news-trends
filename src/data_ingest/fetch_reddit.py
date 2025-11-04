import requests
import pandas as pd
from pathlib import Path
import time

def fetch_reddit_posts(topic="AI"):
    print(f"💬 Fetching Reddit posts for topic: {topic} ...")

    url = f"https://www.reddit.com/search.json?q={topic}&limit=10&sort=hot"
    headers = {"User-Agent": "Mozilla/5.0"}
    output_path = Path(f"data/processed/reddit_{topic.lower().replace(' ', '_')}.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                print(f"❌ Reddit API HTTP {res.status_code}: {res.text}")
                time.sleep(2)
                continue

            data = res.json()
            posts = data.get("data", {}).get("children", [])
            if not posts:
                print("⚠️ No Reddit data fetched.")
                return None

            records = []
            for p in posts:
                d = p["data"]
                records.append({
                    "title": d.get("title"),
                    "url": f"https://reddit.com{d.get('permalink')}",
                    "score": d.get("score"),
                    "subreddit": d.get("subreddit"),
                    "source_type": "reddit"
                })

            df = pd.DataFrame(records)
            df.to_csv(output_path, index=False)
            print(f"✅ Saved {len(df)} Reddit posts → {output_path}")
            return str(output_path)

        except Exception as e:
            print(f"⚠️ Reddit fetch failed: {e}")
            time.sleep(2)

    print("⚠️ No Reddit data fetched after 3 retries.")
    return None
