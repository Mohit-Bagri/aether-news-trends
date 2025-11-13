# === response_engine.py ===
# Handles LLM replies and tone detection for Aether

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ---------------------------------------------------------
# 🔹 MAIN LLM RESPONSE GENERATOR (supports resume)
# ---------------------------------------------------------
def generate_llm_response(intent, tone, user_input, prefix=None, remaining=None, resume=False):
    """
    If resume=True → we DO NOT call OpenAI again.
    We simply return the remaining text.
    """

    # -----------------------------------------------------
    # 🔥 1. HANDLE RESUME CONTINUATION FIRST
    # -----------------------------------------------------
    if resume:
        # remaining is what frontend saved during typewriter
        continued_text = remaining or ""

        return {
            "status": "success",
            "resume": True,          # <-- important
            "results": [
                {"source_type": "aether_reply", "title": continued_text}
            ]
        }

    # -----------------------------------------------------
    # 🔥 2. NORMAL GENERATION (NO RESUME)
    # -----------------------------------------------------
    if not OPENAI_API_KEY:
        return {
            "status": "error",
            "results": [{"source_type": "aether_reply",
                         "title": "⚠️ Missing API key. Please check your .env file."}]
        }

    # --- SYSTEM PROMPT ---
    system_prompt = f"""
You are Aether — a helpful, human-like AI companion.
Current persona tone: {tone}
Current intent: {intent.capitalize()}

Respond naturally in 1–2 paragraphs.

Tone rules:
- sarcastic: dry humor, light mocking
- roast: playful savage but NOT hateful
- genz: casual TikTok Gen-Z chaos
- dark_humor: edgy but not harmful
- cold: emotionless, logical
- wholesome: uplifting, soft
- bollywood: dramatic, filmy
- ultra_nerd: hyper technical
- shakespeare: thee-thou poetic style

Avoid disclaimers and system-style text.
"""

    user_prompt = f"User said: {user_input}\nRespond naturally in {tone} tone."

    try:
        with httpx.Client(timeout=50.0) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt.strip()},
                        {"role": "user", "content": user_prompt.strip()},
                    ],
                    "temperature": 0.8,
                    "max_tokens": 600
                }
            )

        data = response.json()
        print("🔥 RAW OPENAI RESPONSE:", data)   # <— DEBUG HERE

        reply = data["choices"][0]["message"].get("content", "").strip()
       
    except Exception as e:
        print("❌ OPENAI ERROR:", str(e))
        reply = f"❌ OpenAI failed: {str(e)}"

     # -----------------------------------------------------
    # 🔥 3. ENSURE FUNCTION ALWAYS RETURNS VALID STRUCTURE
    # -----------------------------------------------------
    return {
        "status": "success",
        "results": [
            {"source_type": "aether_reply", "title": reply}
        ]
    }



# ---------------------------------------------------------
# 🎭 TONE DETECTION — FIXED
# ---------------------------------------------------------
def detect_tone_change(user_message: str):
    msg = user_message.lower().strip()

    tone_map = {
        "casual": ["casual", "friendly", "chill", "talk normally"],
        "professional": ["professional", "formal", "business"],
        "comic": [
            "comic", "funny", "humorous", "funniest",
            "make me laugh", "be funny", "joke",
            "fun way", "funniest way", "crack me up",
            "make it hilarious", "hilarious", "in the funniest way",
            "tell in a funny way"
        ],
        "empathetic": ["empathetic", "kind", "understanding"],
        "creative": ["creative", "artistic", "imaginative"],
        "analytical": ["analytical", "logical", "rational"],
        "professor": ["professor", "teacher", "academic", "phd"],
        "confident": ["confident", "assertive", "bold"],
        "sarcastic": ["sarcastic", "sarcasm", "be sarcastic"],
        "roast": ["roast", "roast me", "insult me", "destroy me"],
        "genz": ["genz", "gen z", "sigma", "skibidi", "rizz", "npc talk"],
        "dark_humor": ["dark humor", "dark-humor", "dark jokes"],
        "cold": ["cold", "emotionless", "robotic", "heartless"],
        "wholesome": ["wholesome", "comforting", "kind-hearted"],
        "bollywood": ["bollywood", "dramatic", "filmy"],
        "ultra_nerd": ["ultra nerd", "scientific", "hyper technical"],
        "shakespeare": ["shakespeare", "bard", "old english", "elizabethan"],
    }

    for tone, words in tone_map.items():
        if any(w in msg for w in words):
            return tone
    return None


# ---------------------------------------------------------
# 🧭 Query Refinement — unchanged
# ---------------------------------------------------------
def refine_search_query(raw_query: str):
    if not OPENAI_API_KEY:
        return raw_query

    system_prompt = (
        "Rewrite the user input into a short, API-friendly search phrase."
    )

    user_prompt = f"User query: '{raw_query}'\nReturn only the refined phrase."

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}",
                         "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 25,
                    "temperature": 0.4,
                },
            )

        data = response.json()
        refined = data["choices"][0]["message"]["content"]
        return refined.strip()
    except:
        return raw_query
