"""
Anti-spam simple basé sur un cooldown en mémoire par utilisateur.
Suffisant pour une instance unique du bot (Render/Railway/VPS).
"""

import time
from config import ANTI_SPAM_COOLDOWN

_last_request = {}


def is_rate_limited(user_id: int) -> bool:
    """Retourne True si l'utilisateur doit attendre avant une nouvelle requête."""
    now = time.time()
    last = _last_request.get(user_id, 0)
    if now - last < ANTI_SPAM_COOLDOWN:
        return True
    _last_request[user_id] = now
    return False


def seconds_remaining(user_id: int) -> float:
    now = time.time()
    last = _last_request.get(user_id, 0)
    return max(0.0, ANTI_SPAM_COOLDOWN - (now - last))

