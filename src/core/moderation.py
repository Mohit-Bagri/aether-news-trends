# src/core/moderation.py
# Lightweight moderation — NO transformers required

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
    return False
