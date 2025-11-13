# === __init__.py ===
# Unified interface for all data ingestion modules

from .fetch_news import fetch_news as fetch_news_data
from .fetch_youtube import fetch_youtube_videos as fetch_youtube_data
from .fetch_reddit import fetch_reddit_posts as fetch_reddit_data


def get_news(query: str):
    """Return list[dict] of relevant news articles."""
    try:
        df = fetch_news_data(query)
        if hasattr(df, "to_dict"):
            return df.to_dict(orient="records")
        elif isinstance(df, list):
            return df
        return []
    except Exception as e:
        print(f"[News Fetch Error] {e}")
        return []


def get_youtube(query: str):
    """Return list[dict] of relevant YouTube videos."""
    try:
        df = fetch_youtube_data(query)
        if hasattr(df, "to_dict"):
            return df.to_dict(orient="records")
        elif isinstance(df, list):
            return df
        return []
    except Exception as e:
        print(f"[YouTube Fetch Error] {e}")
        return []


def get_reddit(query: str):
    """Return list[dict] of relevant Reddit posts."""
    try:
        df = fetch_reddit_data(query)
        if hasattr(df, "to_dict"):
            return df.to_dict(orient="records")
        elif isinstance(df, list):
            return df
        return []
    except Exception as e:
        print(f"[Reddit Fetch Error] {e}")
        return []
