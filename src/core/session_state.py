# === session_state.py ===
# Keeps persona mode + lightweight memory for "more posts" continuation

persona_state = {
    "persona": "Neutral",
    "persona_mode": "casual",  # default conversational mode
}

# Memory to track last search + offset for pagination
memory_state = {
    "last_query": None,
    "news_offset": 0,
    "reddit_offset": 0,
    "youtube_offset": 0,
}

# Last bot message (full text)
_last_bot_message = {"text": "", "partial": ""}


# -------- Persona --------
def get_persona():
    return persona_state.get("persona", "Neutral")


def set_persona(p):
    persona_state["persona"] = p


def get_mode():
    return persona_state.get("persona_mode", "casual")


def set_mode(mode):
    persona_state["persona_mode"] = mode


# -------- Memory Tracking --------
def remember_query(query):
    memory_state["last_query"] = query
    memory_state["news_offset"] = 0
    memory_state["reddit_offset"] = 0
    memory_state["youtube_offset"] = 0


def get_last_query():
    return memory_state.get("last_query")


def increment_offset(source_type, step=5):
    key = f"{source_type}_offset"
    if key in memory_state:
        memory_state[key] += step


def get_offset(source_type):
    return memory_state.get(f"{source_type}_offset", 0)


# -------- Last bot message helpers --------
def set_last_bot_message(text: str):
    _last_bot_message["text"] = text or ""
    # reset partial
    _last_bot_message["partial"] = ""


def get_last_bot_message():
    return _last_bot_message["text"]


def set_partial_bot_message(prefix: str, remaining: str):
    # store both for potential debugging / recovery
    _last_bot_message["text"] = (prefix or "") + (remaining or "")
    _last_bot_message["partial"] = {"prefix": prefix or "", "remaining": remaining or ""}


def get_partial_bot_message():
    return _last_bot_message.get("partial", {"prefix": "", "remaining": ""})
