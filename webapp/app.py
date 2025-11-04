from flask import Flask, render_template, request, jsonify
import pandas as pd
from pathlib import Path
from src.data_ingest.fetch_news import fetch_news
from src.data_ingest.fetch_youtube import fetch_youtube_videos
from src.data_ingest.fetch_reddit import fetch_reddit_posts
from src.data_cleaning.merge_all_sources import merge_all_sources  # if you have this
import traceback

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        topic = data.get("message", "").strip()
        if not topic:
            return jsonify({"status": "error", "error": "No topic provided"})

        print(f"🧠 User asked: {topic}")

        # --- Fetch all data sources ---
        news_path = fetch_news(topic)
        yt_path = fetch_youtube_videos(topic)
        reddit_path = fetch_reddit_posts(topic)

        results = []

        # --- Process news ---
        if news_path and Path(news_path).exists():
            df_news = pd.read_csv(news_path)
            for _, row in df_news.head(5).iterrows():
                results.append({
                    "title": row.get("title", "Untitled"),
                    "url": row.get("url", ""),
                    "source_type": "news"
                })

        # --- Process YouTube ---
        if yt_path and Path(yt_path).exists():
            df_yt = pd.read_csv(yt_path)
            for _, row in df_yt.head(5).iterrows():
                results.append({
                    "title": row.get("title", "Untitled"),
                    "url": row.get("url", ""),
                    "source_type": "youtube"
                })

        # --- Process Reddit ---
        if reddit_path and isinstance(reddit_path, str) and Path(reddit_path).exists():
            df_reddit = pd.read_csv(reddit_path)
            for _, row in df_reddit.head(5).iterrows():
                results.append({
                    "title": row.get("title", "Untitled"),
                    "url": row.get("url", ""),
                    "source_type": "reddit"
                })

        if not results:
            return jsonify({
                "status": "success",
                "topic": topic,
                "summary": f"No detailed results found for {topic}.",
                "results": []
            })

        return jsonify({
            "status": "success",
            "topic": topic,
            "summary": f"Found {len(results)} items related to '{topic}'. Top results:",
            "results": results
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"status": "error", "error": str(e)})


if __name__ == "__main__":
    print("✅ Aether Flask running on http://127.0.0.1:5000")
    app.run(debug=True)
