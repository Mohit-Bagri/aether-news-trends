import os
import requests
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from src.llm.response_engine import refine_search_query


load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def _iso8601_duration_to_seconds(dur):
    if not dur or not dur.startswith("PT"):
        return 0
    h = m = s = 0
    num = ""
    for ch in dur[2:]:
        if ch.isdigit():
            num += ch
        else:
            if ch == "H":
                h = int(num or 0)
            elif ch == "M":
                m = int(num or 0)
            elif ch == "S":
                s = int(num or 0)
            num = ""
    return h * 3600 + m * 60 + s


def _is_relevant(text: str, topic: str):
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

    tokens = re.sub(r"[^a-z0-9\s]", " ", text).split()
    proximity_hits = 0
    for i in range(len(tokens) - 1):
        if tokens[i] in topic_words:
            for j in range(i + 1, min(i + 7, len(tokens))):
                if tokens[j] in topic_words and tokens[j] != tokens[i]:
                    proximity_hits += 1
                    break

    return (score >= 2 or proximity_hits >= 1 or similar) if len(topic_words) >= 2 else (score >= 1 or similar)


def fetch_youtube_videos(query="news", max_results=20):
    """Fetch YouTube videos as list[dict] compatible with Aether’s pipeline."""
    print(f"🎥 YouTube: Fetching videos for '{query}'...")
    # query is already refined by intent handler
    query = query.strip()

    print(f"🔍 Refined YouTube topic: {query}")

    if not YOUTUBE_API_KEY:
        print("❌ Missing YOUTUBE_API_KEY")
        return []

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    query_variants = list(dict.fromkeys([
        query,
        query.split()[0],
        query.split()[-1],
        re.sub(r"operation\s+", "", query, flags=re.I),
    ]))

    def _search_youtube(q, duration="any"):
        params = {
            "q": q,
            "type": "video",
            "part": "snippet",
            "maxResults": max_results,
            "order": "relevance",
            "publishedAfter": week_ago.isoformat(),
            "videoDuration": duration,
            "relevanceLanguage": "en",
            "regionCode": "US",
            "key": YOUTUBE_API_KEY,
        }
        try:
            r = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            return [i["id"]["videoId"] for i in data.get("items", []) if "videoId" in i["id"]]
        except Exception as e:
            print(f"⚠️ YouTube search failed for '{q}' ({duration}): {e}")
            return []

    all_ids = []
    for q in query_variants:
        ids = _search_youtube(q, "medium") or _search_youtube(q, "long") or _search_youtube(q, "any")
        all_ids.extend(ids)
        if len(all_ids) >= 5:
            break

    all_ids = list(dict.fromkeys(all_ids))
    if not all_ids:
        print("⚠️ YouTube: No results found after all variants")
        return []

    params = {"part": "statistics,snippet,contentDetails", "id": ",".join(all_ids[:50]), "key": YOUTUBE_API_KEY}

    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"❌ YouTube details failed: {e}")
        return []

    videos = []
    for item in data.get("items", []):
        sn = item.get("snippet", {})
        st = item.get("statistics", {})
        cd = item.get("contentDetails", {})

        title = sn.get("title", "").strip()
        desc = sn.get("description", "")
        channel = sn.get("channelTitle", "")
        published_at = sn.get("publishedAt")
        duration_sec = _iso8601_duration_to_seconds(cd.get("duration", ""))
        views = int(st.get("viewCount", 0))

        if not published_at:
            continue

        pub_dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if pub_dt < week_ago or duration_sec < 60:
            continue

        combined = f"{title} {desc} {channel}"
        if not _is_relevant(combined, query):
            continue

        hours = max(1, int((now - pub_dt).total_seconds() // 3600))
        published_str = f"{hours}h ago" if hours < 24 else pub_dt.strftime("%Y-%m-%d")

        videos.append({
            "source_type": "youtube",
            "title": title,
            "channel": channel,
            "published": published_str,
            "views": views,
            "url": f"https://www.youtube.com/watch?v={item['id']}",
        })

    if not videos:
        print("⚠️ Filtered out all YT videos after relevance check")
        return []

    # === SMART RELEVANCE & ENGAGEMENT SCORING ===
    query_lower = query.lower().strip()
    query_keywords = [w for w in re.findall(r"\w+", query_lower)]

    def _score_video(v):
        """Compute a weighted score for relevance + engagement."""
        title = v.get("title", "").lower()
        channel = v.get("channel", "").lower()

        # ✅ 1. Title and channel keyword matches (weighted)
        keyword_hits = sum(k in title for k in query_keywords) * 3
        keyword_hits += sum(k in channel for k in query_keywords) * 2

        # ✅ 2. Engagement score (views in hundreds of thousands)
        view_boost = min(v.get("views", 0) / 200_000, 5)  # scaled 0–5

        # ✅ 3. Recency bonus (prefer newer videos)
        recent_bonus = 0
        if v["published"].endswith("ago"):
            try:
                hours_ago = int(v["published"].split("h")[0])
                recent_bonus = max(0, 3 - (hours_ago / 12))  # fades after ~36h
            except:
                pass

        return keyword_hits + view_boost + recent_bonus

    # 🧠 Optional: boost exact channel match
    for v in videos:
        if query_lower in v.get("channel", "").lower():
            v["views"] *= 2  # stronger weight for exact creator

    # Score and sort
    videos.sort(key=_score_video, reverse=True)

    # Filter out weakly relevant results
    videos = [v for v in videos if _score_video(v) >= 2]

    # Limit to top results
    videos = videos[:max_results]

    print(f"✅ YouTube: {len(videos)} ranked videos (top={videos[0]['title'][:60]}...)")
    return videos
