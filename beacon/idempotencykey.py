"""Idempotency keys: a retried request within the window acts once and returns the first result.

A client that sends a request, loses the network before the response
arrives, and retries has no way to know whether the first attempt
took effect, so without protection a retry can double-charge, double-
register, double-send. An idempotency key makes the retry safe. The
client attaches a unique key to the request, the server remembers the
key along with the result it produced, and a later request carrying
the same key is not executed again, it returns the stored result of
the first, so the operation happens exactly once no matter how many
times it is retried. The protection has a boundary the module makes
explicit: the server cannot remember keys forever, so it keeps them
for a window, and a repeat arriving after the window has expired
finds no record and is executed as new. The window must therefore be
set longer than the longest a client could reasonably retry, or the
guarantee has a hole exactly where a slow retry falls through. The
module stores keys with their result and time, returns the cached
result for a repeat inside the window, executes and records a genuine
first request, and treats an expired repeat as new.
"""

from __future__ import annotations

from beacon.errors import Invalid


class IdempotencyStore:
    def __init__(self, window: int) -> None:
        if window <= 0:
            raise Invalid(
                "a zero window remembers no key, so every retry "
                "re-executes; there is no idempotency to provide"
            )
        self.window = window
        self.seen: dict[str, tuple[str, int]] = {}

    def process(self, key: str, now: int, result: str) -> tuple[str, str]:
        record = self.seen.get(key)
        if record is not None and now - record[1] < self.window:
            return ("cached", record[0])
        self.seen[key] = (result, now)
        return ("executed", result)
