# === summarizer.py ===
# Aether’s Briefing — minimal, clean, aesthetic

import os
import re
import requests
import random
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

HF_API_KEY = os.getenv("HF_API_KEY")


# ---------------------------
# Optional helpers
# ---------------------------
def _fmt_time(dt):
    if not dt:
        return ""
    if isinstance(dt, datetime):
        now = datetime.now(timezone.utc)
        diff = now - dt
        hrs = int(diff.total_seconds() // 3600)
        return f"{hrs}h ago" if hrs < 24 else dt.strftime("%Y-%m-%d")
    return str(dt)


# ---------------------------
# Main summarizer
# ---------------------------
def summarize_results(news_list=None, reddit_list=None, youtube_list=None, tone="casual", topic=""):
    """
    Clean, modern briefing:
    - Only News + YouTube
    - Random 5 headlines max
    - Aether’s Take (2 lines)
    """
    news_list = news_list or []
    youtube_list = youtube_list or []

    # ------------------------------------------
    # Collect only news & youtube titles
    # ------------------------------------------
    all_posts = []

    for item in news_list:
        t = (item.get("title") or "").strip()
        if len(t) >= 5:
            all_posts.append({"title": t, "tag": "(NEWS)"})

    for item in youtube_list:
        t = (item.get("title") or "").strip()
        if len(t) >= 5:
            all_posts.append({"title": t, "tag": "(YouTube)"})

    # ------------------------------------------
    # Dedupe titles
    # ------------------------------------------
    seen = set()
    cleaned = []

    for p in all_posts:
        key = p["title"].lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(p)

    random.shuffle(cleaned)
    cleaned = cleaned[:5]

    # ------------------------------------------
    # If nothing found
    # ------------------------------------------
    if not cleaned:
        return {
            "source_type": "summary",
            "title": "Aether's Briefing",
            "description": "No relevant posts found."
        }

    # ------------------------------------------
    # Build final briefing body (NO duplicate title)
    # ------------------------------------------
    bullet_lines = []
    for p in cleaned:
        bullet_lines.append(f"• {p['title']} {p['tag']}")

    # ------------------------------------------
    # Aether’s Take — clean 2 lines
    # ------------------------------------------
    take_prompt = (
        f"Write a reflective two-line take about '{topic}'. "
        "No bullets. No summary of headlines. Philosophical tone."
    )

    try:
        import httpx
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        if OPENAI_API_KEY:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Return exactly two lines. No bullets."},
                        {"role": "user", "content": take_prompt},
                    ],
                    "max_tokens": 45,
                    "temperature": 0.7
                },
                timeout=10
            )

            take_raw = resp.json()["choices"][0]["message"]["content"].strip()
        else:
            take_raw = "AI evolves quickly, but meaning evolves slowly.\nWhat we choose to build defines us more than the tech itself."

    except:
        take_raw = "AI evolves quickly, but meaning evolves slowly.\nWhat we choose to build defines us more than the tech itself."

    # Ensure exactly **2 cleaned lines**
    take_lines = [line.strip() for line in take_raw.split("\n") if line.strip()]
    take_lines = take_lines[:2]
    if len(take_lines) == 1:
        take_lines.append("")  # fill second line if missing

    take_final = "\n".join(take_lines)

    # ------------------------------------------
    # Final description (frontend parses this cleanly)
    # ------------------------------------------
    description = (
        "**Aether's Briefing**\n\n"
        + "\n".join(bullet_lines)
        + "\n\n✨ **Aether's Take:**\n"
        + take_final
    ).strip()

    # ------------------------------------------
    # Return final card
    # ------------------------------------------
    return {
        "source_type": "summary",
        "title": "Aether's Briefing",
        "description": description,
    }
