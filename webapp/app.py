# === app.py ===
# Aether Backend Entry Point

from flask import Flask, render_template, Response, send_from_directory
import sys, os, traceback, threading, json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import math

# --- Dynamic Path Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

# --- Import Modules ---
from src.data_ingest.fetch_news import fetch_news
from src.data_ingest.fetch_youtube import fetch_youtube_videos
from src.data_ingest.fetch_reddit import fetch_reddit_posts
from src.summary.summarizer import summarize_results
from src.core.moderation import is_disallowed
from src.llm.response_engine import generate_llm_response
from src.core.intent import handle_intent

# --- Safe Chat Blueprint Import ---
try:
    from webapp.routes.chat import chat_bp
except Exception as e:
    chat_bp = None
    print(f"⚠️ chat_bp import failed: {e}")

# --- Flask Setup ---
template_path = os.path.join(PROJECT_ROOT, "webapp", "templates")
static_path = os.path.join(PROJECT_ROOT, "webapp", "static")

app = Flask(__name__, template_folder=template_path, static_folder=static_path)
executor = ThreadPoolExecutor(max_workers=3)
abort_flags = {}

# === Register Blueprint ===
if chat_bp:
    try:
        app.register_blueprint(chat_bp)
        print("✅ Registered chat blueprint successfully.")
    except Exception as e:
        print(f"⚠️ Failed to register chat blueprint: {e}")
else:
    print("⚠️ chat_bp not available. Using fallback routes only.")

# --- Conversation Memory ---
conversation_history = deque(maxlen=8)
last_topic_map = {}

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )

# --- Utilities ---
def format_time(published_at):
    """Return readable time like '5h ago' or ISO date fallback."""
    if not published_at:
        return ""
    try:
        if isinstance(published_at, str):
            if published_at.endswith("Z"):
                published_at = published_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(published_at)
        else:
            dt = published_at
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        diff = now - dt.astimezone(timezone.utc)
        hours = int(diff.total_seconds() // 3600)
        return f"{hours}h ago" if hours < 24 else dt.strftime("%Y-%m-%d")
    except Exception:
        return str(published_at)

def remember_exchange(user_msg: str, bot_reply: str):
    conversation_history.append({"user": user_msg or "", "bot": bot_reply or ""})

def summarize_memory():
    if not conversation_history:
        return ""
    items = [f"User: {h['user']}\nAether: {h['bot']}" for h in conversation_history]
    return "\n".join(items[-5:])

def to_safe_value(v):
    """Ensure all values are JSON-safe."""
    try:
        if v is None:
            return ""
        if hasattr(v, "isoformat"):
            return v.isoformat()
        if isinstance(v, (int, float)):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                return ""
            return v
        return str(v)
    except Exception:
        return str(v)

# --- Routes ---
@app.route("/")
def index():
    """Serve the chat UI."""
    return render_template("index.html")

@app.route("/abort", methods=["POST"])
def abort():
    """Stop current generation safely."""
    tid = threading.get_ident()
    abort_flags[tid] = True
    print(f"🛑 Abort flag set for thread {tid}")
    return Response(json.dumps({"status": "aborted"}), mimetype="application/json")

@app.route("/debug_ping")
def debug_ping():
    """Simple ping route to confirm server is running."""
    return {"status": "ok", "message": "Aether backend active."}

# --- Global Error Handler ---
@app.errorhandler(Exception)
def handle_all_exceptions(e):
    print("\n❌ GLOBAL FLASK ERROR — FULL TRACEBACK BELOW:")
    print("=" * 90)
    traceback.print_exc()
    print("=" * 90)
    payload = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
    return Response(json.dumps(payload), mimetype="application/json"), 500

# --- Launch App ---
if __name__ == "__main__":
    port = int(os.environ.get("AETHER_PORT", 5050))
    print("\n" + "=" * 90)
    print(f"🚀 Starting Aether backend on http://127.0.0.1:{port}")
    print(f"📁 Templates: {template_path}")
    print(f"📁 Static: {static_path}")
    print("=" * 90 + "\n")
    app.run(host="127.0.0.1", port=port, debug=True, threaded=True, use_reloader=False)

