import pandas as pd
from pathlib import Path
from datetime import datetime
from src.data_ingest.fetch_news import  fetch_news
from src.data_ingest.fetch_youtube import fetch_youtube_videos as fetch_youtube
from src.data_ingest.fetch_reddit import fetch_reddit_posts as fetch_reddit
from src.data_cleaning.news_data_clean import clean_news_data

def merge_all_sources(topic: str) -> str:
    """
    Fetch & merge data from News, YouTube, and Reddit sources.
    Returns path to final combined CSV.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    final_path = processed_dir / f"final_combined_{topic.lower().replace(' ', '_')}.csv"

    all_dfs = []

    # ------------------------------
    # 📰 NEWS
    # ------------------------------
    try:
        print(f"📰 Fetching fresh news for topic: {topic} ...")
        news_json_path = fetch_news(topic)
        cleaned_news_path = clean_news_data(news_json_path)
        df_news = pd.read_csv(cleaned_news_path)
        df_news["source_type"] = "news"
        all_dfs.append(df_news)
    except Exception as e:
        print(f"❌ News fetch failed: {e}")

    # ------------------------------
    # 🎥 YOUTUBE
    # ------------------------------
    try:
        print(f"🎥 Fetching YouTube videos for topic: {topic} ...")
        df_yt = fetch_youtube(topic)
        if isinstance(df_yt, pd.DataFrame) and not df_yt.empty:
            df_yt["source_type"] = "youtube"
            all_dfs.append(df_yt)
            out_path = processed_dir / f"youtube_{topic.lower().replace(' ', '_')}.csv"
            df_yt.to_csv(out_path, index=False)
            print(f"✅ Saved {len(df_yt)} YouTube videos → {out_path}")
        else:
            print("⚠️ No YouTube data fetched.")
    except Exception as e:
        print(f"❌ YouTube fetch failed: {e}")

    # ------------------------------
    # 💬 REDDIT
    # ------------------------------
    try:
        print(f"💬 Fetching Reddit posts for topic: {topic} ...")
        df_reddit = fetch_reddit(topic)
        if isinstance(df_reddit, pd.DataFrame) and not df_reddit.empty:
            df_reddit["source_type"] = "reddit"
            all_dfs.append(df_reddit)
            out_path = processed_dir / f"reddit_{topic.lower().replace(' ', '_')}.csv"
            df_reddit.to_csv(out_path, index=False)
            print(f"✅ Saved {len(df_reddit)} Reddit posts → {out_path}")
        else:
            print("⚠️ No Reddit data fetched.")
    except Exception as e:
        print(f"❌ Reddit fetch failed: {e}")

    # ------------------------------
    # 🧩 MERGE ALL
    # ------------------------------
    if not all_dfs:
        raise ValueError(f"No data found for topic '{topic}'.")

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df.to_csv(final_path, index=False)
    print(f"✅ Final combined data saved to {final_path} ({len(combined_df)} rows)")

    return str(final_path)
