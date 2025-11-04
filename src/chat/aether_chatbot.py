import pandas as pd
from pathlib import Path
from src.data_cleaning.merge_all_sources import merge_all_sources

def generate_answer(user_query: str):
    try:
        from src.data_cleaning.merge_all_sources import merge_all_sources
        topic = user_query.strip()
        combined_path = merge_all_sources(topic)

        df = pd.read_csv(combined_path)

        # Short summary
        summary = f"Found {len(df)} items related to '{topic}'. Top results:"

        # Take first 5 entries
        results = []
        for _, row in df.head(5).iterrows():
            results.append({
                "title": str(row.get("title", "")),
                "url": str(row.get("url", "")),
            })

        return {
            "status": "success",
            "topic": topic,
            "summary": summary,
            "results": results
        }

    except Exception as e:
        print(f"❌ Error in generate_answer: {e}")
        return {"status": "error", "error": str(e)}
