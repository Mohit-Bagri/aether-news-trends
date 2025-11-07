from flask import Flask, render_template, request, jsonify
from src.data_ingest.fetch_news import fetch_news
from src.data_ingest.fetch_youtube import fetch_youtube_videos
from src.data_ingest.fetch_reddit import fetch_reddit_posts
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

app = Flask(__name__, template_folder="templates", static_folder="static")

# Use a global thread pool for parallel data fetching
executor = ThreadPoolExecutor(max_workers=3)

# === Utility ===
def format_time(published_at):
    """Return readable time format like '5h ago' or '2025-11-05'."""
    if not published_at:
        return ""
    if isinstance(published_at, str):
        try:
            if published_at.endswith("Z"):
                published_at = published_at.replace("Z", "+00:00")
            published_at = datetime.fromisoformat(published_at).astimezone(timezone.utc)
        except Exception:
            return published_at
    now = datetime.now(timezone.utc)
    diff = now - published_at
    hours = int(diff.total_seconds() // 3600)
    return f"{hours}h ago" if hours < 24 else published_at.strftime("%Y-%m-%d")

def client_disconnected():
    """Try to detect if the client has closed the connection."""
    try:
        if hasattr(request, "environ") and request.environ.get("werkzeug.server.shutdown") is None:
            return False
        return False
    except Exception:
        return False

# === Routes ===
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        topic = (data.get("message") or "").strip()
        print(f"📩 /chat endpoint hit for topic: {topic}")

        if not topic:
            return jsonify({"status": "error", "error": "Empty message"})

        # ✅ If user disconnected early
        if client_disconnected():
            print("⚠️ Client disconnected before fetch started.")
            return jsonify({"status": "cancelled"})

        # === Fetch data in parallel ===
        futures = {
            executor.submit(fetch_news, topic): "news",
            executor.submit(fetch_youtube_videos, topic): "youtube",
            executor.submit(fetch_reddit_posts, topic): "reddit",
        }

        results = {"news": None, "youtube": None, "reddit": None}

        for future in as_completed(futures):
            if client_disconnected():
                print("⚠️ Client disconnected mid-fetch. Cancelling remaining tasks.")
                return jsonify({"status": "cancelled"})

            source = futures[future]
            try:
                results[source] = future.result(timeout=25)
            except Exception as e:
                print(f"⚠️ {source} fetch failed: {e}")

        # ✅ Format results
        combined = []

        df_news, df_yt, df_reddit = results["news"], results["youtube"], results["reddit"]

        if df_news is not None and not df_news.empty:
            for _, row in df_news.head(5).iterrows():
                combined.append({
                    "source_type": "news",
                    "title": row.get("title"),
                    "author": row.get("author"),
                    "url": row.get("url"),
                    "published": format_time(row.get("publishedAt"))
                })

        if df_yt is not None and not df_yt.empty:
            for _, row in df_yt.head(5).iterrows():
                combined.append({
                    "source_type": "youtube",
                    "title": row.get("title"),
                    "channel": row.get("channel"),
                    "views": int(row.get("views", 0)),
                    "url": row.get("url"),
                    "published": format_time(row.get("publishedAt"))
                })

        if df_reddit is not None and not df_reddit.empty:
            for _, row in df_reddit.head(5).iterrows():
                combined.append({
                    "source_type": "reddit",
                    "title": row.get("title"),
                    "subreddit": row.get("subreddit"),
                    "upvotes": int(row.get("upvotes", 0)),
                    "url": row.get("url"),
                    "published": format_time(row.get("publishedAt"))
                })

        print(f"✅ Returning {len(combined)} results for topic: {topic}")
        return jsonify({"status": "success", "topic": topic, "results": combined})

    except Exception:
        print("❌ /chat error:\n", traceback.format_exc())
        return jsonify({"status": "error", "error": "Internal Server Error"})


if __name__ == "__main__":
    print("✅ Aether Flask running at: http://127.0.0.1:5000")
    app.run(debug=True, threaded=True)
