# src/core/moderation.py
from transformers import pipeline

# Initialize optional Hugging Face moderation model
try:
    hf_moderator = pipeline("text-classification", model="facebook/roberta-hate-speech-dynabench-r4-target")
except Exception:
    hf_moderator = None  # Safe fallback if offline

DISALLOWED_PATTERNS = [
    "kill them", "should die", "praise attack", "celebrate deaths",
    "wipe out", "execute", "genocide", "massacre", "deserve to die"
]

def is_disallowed(text: str) -> bool:
    """Check if user message or model output violates safety rules."""
    lower = text.lower()
    for phrase in DISALLOWED_PATTERNS:
        if phrase in lower:
            return True
    if hf_moderator:
        try:
            result = hf_moderator(text[:512])[0]
            if result["label"].lower() in ["offensive", "hate", "toxic"] and result["score"] > 0.7:
                return True
        except Exception:
            pass
    return False
