import os
import json
import re
from datetime import datetime

MEMORY_FILE = os.path.join("data", "session_memory.json")

# ensure data folder exists
os.makedirs("data", exist_ok=True)


def load_memory():
    """Load memory JSON if exists."""
    if not os.path.exists(MEMORY_FILE):
        return {"last_topic": None, "recent_queries": []}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"last_topic": None, "recent_queries": []}


def save_memory(memory):
    """Persist memory state to JSON."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def update_memory(new_query: str):
    """Update last topic and history."""
    memory = load_memory()
    memory["last_topic"] = new_query
    memory["recent_queries"].append({"query": new_query, "time": datetime.now().isoformat()})

    # keep only last 5
    memory["recent_queries"] = memory["recent_queries"][-5:]
    save_memory(memory)


def infer_continued_query(user_input: str):
    """
    Infer full query based on conversation context.
    Handles follow-ups like 'and NVIDIA?' or 'what about Tesla?'
    Resets when a new domain appears.
    """
    memory = load_memory()
    last_topic = memory.get("last_topic")
    query = user_input.strip()

    if not last_topic:
        update_memory(query)
        return query

    # --- detect follow-up style prompts ---
    if re.match(r"^(and|what about|continue|more on|tell me about)", query, re.I):
        combined = f"{last_topic} {query}"
        update_memory(combined)
        print(f"🧠 Continuing context: '{last_topic}' → '{combined}'")
        return combined

    # --- detect unrelated new topic ---
    overlap = len(set(query.lower().split()) & set(last_topic.lower().split()))
    if overlap == 0:
        update_memory(query)
        print(f"🧹 New topic detected: '{query}' (reset context)")
        return query

    # --- partial overlap = semi-related continuation ---
    combined = f"{last_topic} {query}"
    update_memory(combined)
    print(f"🔗 Partial continuation: '{combined}'")
    return combined
