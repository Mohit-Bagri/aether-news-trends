# === intent.py ===
# Detects what user wants and routes to right response generator

import concurrent.futures
import difflib
import random
import datetime

from src.data_ingest.fetch_news import fetch_news
from src.data_ingest.fetch_reddit import fetch_reddit_posts as fetch_reddit
from src.data_ingest.fetch_youtube import fetch_youtube_videos as fetch_youtube
from src.llm.response_engine import generate_llm_response, detect_tone_change, refine_search_query
from src.summary.summarizer import summarize_results
from src.core.session_state import (
    set_mode,
    get_mode,
    remember_query,
    get_last_query,
    increment_offset,
    get_offset,
)

# -------------------------
# Helpers for intent parsing
# -------------------------

QUESTION_WORDS = ("when", "where", "who", "what", "why", "how", "which", "whom", "whose")
INTENTAL_PHRASES = ("show me", "latest", "recent", "play", "watch", "videos", "channel", "list", "find", "search", "give me")
VIDEO_KEYWORDS = ("youtube", "video", "yt", "clip", "upload", "vlog", "interview")
REDDIT_KEYWORDS = ("reddit", "thread", "discussion", "upvotes", "r/")
NEWS_KEYWORDS = ("news", "headline", "article", "story", "update")


def _looks_like_question(msg: str) -> bool:
    m = msg.strip().lower()
    if "?" in m:
        return True
    if any(m.startswith(w + " ") for w in QUESTION_WORDS):
        return True
    if any(
        phrase in m
        for phrase in ["when will ", "will ", "is going to ", "when does ", "when did "]
    ):
        return True
    return False


def _wants_to_browse_media(msg: str) -> bool:
    m = msg.lower()
    if _looks_like_question(m):
        return False
    if any(phrase in m for phrase in INTENTAL_PHRASES):
        return True
    if any(k in m for k in VIDEO_KEYWORDS):
        return True
    return False


def _wants_reddit_fetch(msg: str) -> bool:
    m = msg.lower()
    if _looks_like_question(m):
        return False
    if any(k in m for k in REDDIT_KEYWORDS):
        return True
    return False


def _wants_news_fetch(msg: str) -> bool:
    m = msg.lower()
    if _looks_like_question(m):
        return False
    if any(k in m for k in NEWS_KEYWORDS):
        return True
    return False


# -----------------------------------------------------------
# 🧠 Intent classification
# -----------------------------------------------------------
def classify_intent(user_message: str) -> str:
    msg = (user_message or "").strip().lower()

    if not msg:
        return "chat"

    if "more" in msg:
        if any(w in msg for w in ["youtube", "video", "yt"]):
            return "youtube_more"
        if "reddit" in msg:
            return "reddit_more"
        if any(w in msg for w in ["news", "article"]):
            return "news_more"

    if "only" in msg or "just" in msg:
        if any(w in msg for w in ["news", "article", "headline"]):
            return "news_only"
        if any(w in msg for w in ["reddit", "thread", "discussion"]):
            return "reddit_only"
        if any(w in msg for w in ["youtube", "yt", "video", "clip"]):
            return "youtube_only"

    if _wants_news_fetch(msg):
        return "news"
    if _wants_to_browse_media(msg):
        return "youtube"
    if _wants_reddit_fetch(msg):
        return "reddit"

    if any(w in msg for w in ["reddit", "discussion", "thread"]):
        return "reddit"
    if any(w in msg for w in ["news", "headline", "update", "story"]):
        return "news"
    if any(w in msg for w in ["youtube", "video", "yt", "clip", "watch", "interview"]):
        return "youtube"

    if any(
        w in msg
        for w in ["explain", "what is", "tell me about", "define", "who is", "when will", "will"]
    ):
        return "chat"

    return "chat"


# -----------------------------------------------------------
# 🧮 Smart Relevance Scoring
# -----------------------------------------------------------
def score_relevance(items, query, key_fields=("title", "description")):
    if not items:
        return []

    q = (query or "").lower()
    now = datetime.datetime.utcnow()

    def parse_date(dt_str):
        try:
            if not dt_str:
                return 0
            if isinstance(dt_str, datetime.datetime):
                dt = dt_str
            else:
                dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            diff_days = (now - dt).days
            return max(0, 90 - diff_days) / 90
        except Exception:
            return 0

    def normalize_engagement(item):
        if "views" in item:
            val = item.get("views")
            if isinstance(val, str) and val.replace(",", "").isdigit():
                val = int(val.replace(",", ""))
            if isinstance(val, (int, float)):
                return min(1.0, val / 1_000_000)
        if "upvotes" in item:
            val = item.get("upvotes")
            if isinstance(val, str) and val.replace(",", "").isdigit():
                val = int(val.replace(",", ""))
            if isinstance(val, (int, float)):
                return min(1.0, val / 10_000)
        return 0

    for item in items:
        text = " ".join(str(item.get(k, "")) for k in key_fields).lower()
        text_score = difflib.SequenceMatcher(None, q, text[:400]).ratio()
        engagement_score = normalize_engagement(item)
        recency_score = parse_date(item.get("published"))

        if "views" in item:
            item["_score"] = (
                0.45 * text_score + 0.40 * engagement_score + 0.15 * recency_score
            )
        elif "upvotes" in item:
            item["_score"] = (
                0.50 * text_score + 0.30 * engagement_score + 0.20 * recency_score
            )
        else:
            item["_score"] = 0.70 * text_score + 0.30 * recency_score

    return sorted(items, key=lambda x: x.get("_score", 0), reverse=True)


# -----------------------------------------------------------
# 🎯 Intent Handler (MAIN)
# -----------------------------------------------------------
def handle_intent(intent: str, tone: str, user_message: str):

    # --- SUMMARY HANDLING ---
    summary_triggers = [
        "summarize that",
        "summarize this",
        "summarize above",
        "summarize previous",
        "summarize the above",
        "summarise",
        "summary please",
    ]

    lower_msg = user_message.lower().strip()

    if any(t in lower_msg for t in summary_triggers):
        from src.core.session_state import get_last_bot_message

        last = get_last_bot_message()
        if not last:
            return {
                "status": "success",
                "results": [
                    {"source_type": "aether_reply", "title": "⚠️ I don’t have anything to summarize yet!"}
                ],
            }

        prompt = f"Summarize the following into 2 simple lines:\n\n{last}"
        return generate_llm_response("chat", tone, prompt)

    # empty query
    if not user_message.strip():
        return {
            "status": "error",
            "results": [{"source_type": "aether_reply", "title": "⚠️ Please type something for me to respond to!"}],
        }

    # tone switching
    tone_change = detect_tone_change(user_message)
    if tone_change:
        set_mode(tone_change)
        tone_response = {
            "source_type": "aether_reply",
            "title": f"🎭 Switched to {tone_change.title()} mode — let's continue!",
        }

        generated = generate_llm_response("chat", tone_change, user_message)

    # safe fallback
        if not generated or "results" not in generated:
            return {"status": "success", "results": [tone_response]}

        return {"status": "success", "results": [tone_response] + generated["results"]}


    if not intent:
        intent = classify_intent(user_message)
    if not tone:
        tone = get_mode()

    print(f"🧩 Intent: {intent} | Tone: {tone}")

    remember_query(user_message)

    # -----------------------------------------------------------
    # Query refinement (except news)
    # -----------------------------------------------------------
    if intent in ("news", "news_only", "news_more"):
        refined_message = user_message.strip()
    else:
        refined_message = refine_search_query(user_message)

    print(f"✨ Refined topic: {refined_message}")

    # -----------------------------------------------------------
    # PAGINATION ("more")
    # -----------------------------------------------------------
    if intent.endswith("_more"):
        last_query = get_last_query()
        if not last_query:
            return {
                "status": "success",
                "results": [{"source_type": "aether_reply", "title": "⚠️ No previous topic to expand."}],
            }

        source = intent.replace("_more", "")
        increment_offset(source)
        offset = get_offset(source)

        fetch_map = {"news": fetch_news, "reddit": fetch_reddit, "youtube": fetch_youtube}
        func = fetch_map.get(source)

        data_list = func(last_query) or []
        data_list = score_relevance(data_list, last_query)

        chunk = data_list[offset : offset + 5]
        return {"status": "success", "results": chunk}

    # -----------------------------------------------------------
    # NEWS INTENT
    # -----------------------------------------------------------
    if intent in ("news", "news_only"):
        news_list = fetch_news(refined_message, max_articles=30) or []
        news_scored = score_relevance(news_list, refined_message)
        news_final = news_scored[:5]

        if intent == "news_only":
            return {
                "status": "success",
                "results": news_final or [{"source_type": "aether_reply", "title": "⚠️ No news found."}],
            }

        # fetch extras for briefing
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            fr = ex.submit(fetch_reddit, refined_message)
            fy = ex.submit(fetch_youtube, refined_message)
            reddit_list = fr.result() or []
            yt_list = fy.result() or []

        reddit_final = score_relevance(reddit_list, refined_message)[:5]
        yt_final = score_relevance(yt_list, refined_message)[:5]

        # 🚨 FIX: Briefing **only when user didn't explicitly mention reddit OR youtube**
        show_briefing = not any(
            w in lower_msg for w in ["reddit", "youtube", "yt", "video", "clip"]
        )

        final_results = []

        if show_briefing:
            summary_card = summarize_results(news_final, reddit_final, yt_final, tone, refined_message)
            if summary_card:
                summary_card["source_type"] = "briefing"
                final_results.append(summary_card)

        final_results.extend(news_final + reddit_final + yt_final)
        return {"status": "success", "results": final_results}

    # -----------------------------------------------------------
    # REDDIT INTENT
    # -----------------------------------------------------------
    if intent in ("reddit", "reddit_only"):
        reddit_list = fetch_reddit(refined_message) or []
        reddit_final = score_relevance(reddit_list, refined_message)[:5]
        return {
            "status": "success",
            "results": reddit_final or [{"source_type": "aether_reply", "title": "⚠️ No Reddit posts found."}],
        }

    # -----------------------------------------------------------
    # YOUTUBE INTENT
    # -----------------------------------------------------------
    if intent in ("youtube", "youtube_only"):
        yt_list = fetch_youtube(refined_message) or []
        yt_final = score_relevance(yt_list, refined_message)[:5]
        return {
            "status": "success",
            "results": yt_final or [{"source_type": "aether_reply", "title": "⚠️ No YouTube videos found."}],
        }

    # -----------------------------------------------------------
    # DEFAULT → Chat LLM response
    # -----------------------------------------------------------
    return generate_llm_response("chat", tone, user_message)

