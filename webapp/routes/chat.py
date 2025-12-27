# === chat.py ===
# Main chat route for Aether (handles messages from frontend)

from flask import Blueprint, request, jsonify
from src.core.intent import handle_intent, classify_intent as detect_intent
from src.core.session_state import get_mode

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """Main message route — handles ALL messages from frontend including resume."""
    try:
        data = request.get_json() or {}
        user_message = (data.get("message") or "").strip()
        resume = bool(data.get("resume", False))
        prefix = data.get("prefix") or ""
        remaining = data.get("remaining") or ""

        # === Validate message ===
        if not user_message and not resume:
            return jsonify({
                "status": "error",
                "results": [
                    {
                        "source_type": "aether_reply",
                        "title": "Please enter a message."
                        }
                ]
            }), 200

        # === SHOW MORE (append) handling ===
        if data.get("append"):
            topic_type = data.get("type", "news")
            print(f"🔁 [APPEND REQUEST] Loading more {topic_type}...")

            from src.data_ingest import fetch_news, fetch_youtube, fetch_reddit
            try:
                if topic_type == "news":
                    results = fetch_news.fetch_news(user_message or "latest")
                elif topic_type == "youtube":
                    results = fetch_youtube.fetch_youtube_videos(user_message or "latest")
                elif topic_type == "reddit":
                    results = fetch_reddit.fetch_reddit_posts(user_message or "latest")
                else:
                    results = []

                print(f"✅ Successfully fetched {len(results)} {topic_type} results (append).")
                return jsonify({"status": "success", "results": results}), 200

            except Exception as err:
                print(f"⚠️ Error fetching more {topic_type}: {err}")
                return jsonify({
                    "status": "error",
                    "results": [
                        {
                            "source_type": "aether_reply",
                            "title": f"⚠️ Couldn’t load more {topic_type}."
                        }
                    ]
                }), 200

        # === STANDARD / RESUME CHAT FLOW ===
        print(f"🗣️ User said: {user_message} | resume={resume}")

        intent = detect_intent(user_message)
        tone = get_mode()
        print(f"🧩 Intent: {intent} | Tone: {tone}")

        # === RESUME HANDLING (Option 1) ===
        if resume:
            print(f"⏩ Resume request — prefix={len(prefix)} remaining={len(remaining)}")

            # If remaining exists → return continuation ONLY
            if remaining:
                return jsonify({
                    "status": "success",
                    "resume": True,
                    "results": [
                        {"source_type": "aether_reply", "title": remaining}
                    ]
                }), 200

            # Nothing left to type
            return jsonify({
                "status": "success",
                "resume": True,
                "results": [
                    {"source_type": "aether_reply", "title": ""}
                ]
            }), 200

        # === NORMAL FIRST-TIME CALL ===
        response_data = handle_intent(intent, tone, user_message)
        print(f"🤖 Response generated: {response_data}")
        response_data["resume"] = False
        return jsonify(response_data), 200

    except Exception as e:
        print(f"❌ Error in chat route: {e}")
        return jsonify({
            "status": "error",
            "results": [
                {
                    "source_type": "aether_reply",
                    "title": f"Internal error: {str(e)}"
                }
            ]
        }), 500


# === Log events from the frontend ===
@chat_bp.route("/chat_event", methods=["POST"])
def chat_event():
    data = request.get_json(silent=True) or {}
    print(f"🟣 [CHAT EVENT] {data}")
    return ("", 204)
