import os, requests, pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def _iso8601_duration_to_seconds(dur):
    if not dur or not dur.startswith("PT"): return 0
    h = m = s = 0; num = ""
    for ch in dur[2:]:
        if ch.isdigit(): num += ch
        else:
            if ch == "H": h = int(num or 0)
            if ch == "M": m = int(num or 0)
            if ch == "S": s = int(num or 0)
            num = ""
    return h*3600 + m*60 + s

def fetch_youtube_videos(query="news", max_results=20):
    print(f"🎥 YouTube: Fetching videos for '{query}'...")

    if not YOUTUBE_API_KEY:
        print("❌ Missing YOUTUBE_API_KEY")
        return pd.DataFrame()

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    def search_youtube(q, duration):
        params = {
            "q": q, "type": "video", "part": "snippet",
            "maxResults": max_results, "order": "relevance",
            "publishedAfter": week_ago.isoformat(),
            "videoDuration": duration, "relevanceLanguage": "en",
            "regionCode": "US", "key": YOUTUBE_API_KEY
        }

        for attempt in range(3):
            try:
                r = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
                return [i["id"]["videoId"] for i in data.get("items", [])]
            except:
                print(f"⚠️ YT search retry {attempt+1}/3...")

        print("❌ YouTube search failed after retries")
        return []

    ids = search_youtube(query, "medium") or search_youtube(query, "long") or search_youtube(query, "any")
    if not ids:
        print("⚠️ YouTube: No results")
        return pd.DataFrame()

    params = {
        "part": "statistics,snippet,contentDetails",
        "id": ",".join(ids),
        "key": YOUTUBE_API_KEY
    }

    for attempt in range(3):
        try:
            r = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            break
        except:
            print(f"⚠️ YT details retry {attempt+1}/3...")
    else:
        print("❌ YT details failed")
        return pd.DataFrame()

    videos = []
    for item in data.get("items", []):
        sn = item.get("snippet", {})
        st = item.get("statistics", {})
        cd = item.get("contentDetails", {})

        title = sn.get("title", "")
        if not all(ord(c) < 128 for c in title): continue

        pub = sn.get("publishedAt")
        if not pub: continue
        pub = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        if pub < week_ago: continue

        if _iso8601_duration_to_seconds(cd.get("duration", "")) < 60: continue

        videos.append({
            "title": title,
            "channel": sn.get("channelTitle"),
            "publishedAt": pub,
            "views": int(st.get("viewCount", 0)),
            "url": f"https://www.youtube.com/watch?v={item['id']}"
        })

    if not videos: 
        print("⚠️ Filtered out all YT videos")
        return pd.DataFrame()

    df = pd.DataFrame(videos).sort_values(by="views", ascending=False).reset_index(drop=True)
    print(f"✅ YouTube: {len(df)} videos")
    return df
