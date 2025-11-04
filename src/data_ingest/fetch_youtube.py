import os
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def fetch_youtube_videos(topic: str, max_results: int = 5):
    """
    Fetch top YouTube videos for a given topic using YouTube Data API v3.
    Saves a CSV and returns the file path.
    """
    if not YOUTUBE_API_KEY:
        raise ValueError("❌ Missing YOUTUBE_API_KEY in .env file")

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": topic,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "order": "relevance",
        "regionCode": "IN"
    }

    print(f"🎥 Fetching YouTube videos for topic: {topic} ...")
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"❌ YouTube API HTTP {response.status_code}: {response.text}")
        return None

    data = response.json()
    if "error" in data:
        print(f"❌ YouTube API error: {data['error']['message']}")
        return None

    items = data.get("items", [])
    if not items:
        print(f"⚠️ No YouTube videos found for {topic}")
        print("🔍 Debug:", data)
        return None

    videos = []
    for v in items:
        snippet = v["snippet"]
        vid_id = v["id"]["videoId"]
        videos.append({
            "title": snippet["title"],
            "text": snippet["description"],
            "channel": snippet["channelTitle"],
            "url": f"https://www.youtube.com/watch?v={vid_id}",
            "publishedAt": snippet["publishedAt"],
            "source": "youtube"
        })

    df = pd.DataFrame(videos)
    output_path = Path(f"data/processed/youtube_{topic.lower().replace(' ', '_')}.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"✅ Saved {len(df)} YouTube videos → {output_path}")
    return output_path


# Debug usage (only runs when you execute this file directly)
if __name__ == "__main__":
    fetch_youtube_videos("AI news")
