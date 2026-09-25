"""Shared pacing and retry handling for all Gemini calls in outreach."""

import re
import time
from typing import Callable, TypeVar

T = TypeVar("T")

MIN_REQUEST_INTERVAL_SECONDS = 5.0
MAX_TRANSIENT_RETRIES = 8
RATE_LIMIT_BUFFER_SECONDS = 1.5

_last_request_started_at = 0.0


def _pace_request() -> None:
    """Keep Gemini calls below the free-tier per-minute request ceiling."""
    global _last_request_started_at

    now = time.monotonic()
    remaining = MIN_REQUEST_INTERVAL_SECONDS - (now - _last_request_started_at)
    if remaining > 0:
        print(f"Gemini pacing: waiting {remaining:.1f}s...")
        time.sleep(remaining)

    _last_request_started_at = time.monotonic()


def _retry_after_seconds(exc: Exception) -> float | None:
    text = str(exc)

    # Gemini errors commonly contain either retryDelay: '39s' or
    # human-readable text such as "Please retry in 39.75s".
    patterns = (
        r"retryDelay['\"\s:]+([0-9]+(?:\.[0-9]+)?)s",
        r"retry\s+in\s+([0-9]+(?:\.[0-9]+)?)s",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))

    return None


def _is_rate_limit(exc: Exception) -> bool:
    text = str(exc).upper()
    code = getattr(exc, "code", None)
    status_code = getattr(exc, "status_code", None)
    return (
        code == 429
        or status_code == 429
        or "429" in text
        or "RESOURCE_EXHAUSTED" in text
        or "QUOTA EXCEEDED" in text
    )


def _is_transient_server_error(exc: Exception) -> bool:
    text = str(exc).upper()
    code = getattr(exc, "code", None)
    status_code = getattr(exc, "status_code", None)
    return (
        code in {500, 502, 503, 504}
        or status_code in {500, 502, 503, 504}
        or any(token in text for token in ("500", "502", "503", "504", "SERVERERROR", "UNAVAILABLE"))
    )


def call_gemini_with_retry(operation: Callable[[], T], *, label: str = "Gemini") -> T:
    """Run one Gemini request, pacing calls and retrying temporary failures.

    A 429 never advances the outreach pipeline to another lead. The same
    operation is retried after Gemini's requested delay (plus a small buffer).
    """
    transient_attempt = 0

    while True:
        _pace_request()

        try:
            return operation()
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            if _is_rate_limit(exc):
                retry_after = _retry_after_seconds(exc) or 60.0
                wait_for = retry_after + RATE_LIMIT_BUFFER_SECONDS
                print(
                    f"{label}: Gemini rate limit reached. "
                    f"Waiting {wait_for:.1f}s, then retrying the SAME request..."
                )
                time.sleep(wait_for)
                continue

            if _is_transient_server_error(exc):
                transient_attempt += 1
                if transient_attempt > MAX_TRANSIENT_RETRIES:
                    raise

                wait_for = min(10 * (2 ** (transient_attempt - 1)), 60)
                print(
                    f"{label}: temporary Gemini error "
                    f"({transient_attempt}/{MAX_TRANSIENT_RETRIES}). "
                    f"Waiting {wait_for}s before retry..."
                )
                time.sleep(wait_for)
                continue

            raise
