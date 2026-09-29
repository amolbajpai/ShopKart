import threading
import time

from app.config import get_settings

_lock = threading.Lock()
_next_allowed = 0.0


def wait_for_llm_slot() -> None:
    """Sleep so two Gemini calls are not sent back-to-back (free-tier RPM)."""
    gap = max(0.0, float(get_settings().llm_call_gap_seconds))
    if gap <= 0:
        return
    global _next_allowed
    with _lock:
        now = time.monotonic()
        wait = _next_allowed - now
        if wait > 0:
            time.sleep(wait)
            now = time.monotonic()
        _next_allowed = now + gap
