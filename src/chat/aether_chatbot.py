import pandas as pd
from src.data_cleaning.merge_all_sources import merge_all_sources

def generate_answer(user_query: str):
    try:
        topic = user_query.strip()
        combined_path = merge_all_sources(topic)
        df = pd.read_csv(combined_path)

        if df.empty:
            return {"status": "success", "topic": topic, "results": []}

        results = []
        for _, row in df.iterrows():
            results.append({
                "title": str(row.get("title", "")),
                "url": str(row.get("url", "")),
                "source_type": str(row.get("source_type", "news")).lower(),
                "author": str(row.get("author", "")),
                "published": str(row.get("publishedAt", "")),
                "channel": str(row.get("channel", "")),
                "views": str(row.get("views", "")),
                "subreddit": str(row.get("subreddit", "")),
                "upvotes": str(row.get("upvotes", "")),
            })

        return {
            "status": "success",
            "topic": topic,
            "results": results
        }

    except Exception as e:
        print(f"❌ Error in generate_answer: {e}")
        return {"status": "error", "error": str(e)}
