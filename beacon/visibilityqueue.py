"""A visibility-timeout queue: at-least-once delivery, so consumers must be idempotent.

A queue that hands a message to a consumer and deletes it immediately
loses the message if the consumer crashes before finishing, so a
durable queue does the opposite: receiving a message does not remove
it, it hides it for a visibility timeout. The consumer processes the
message and then explicitly deletes it, and if the consumer deletes
it before the timeout the message is gone for good, but if the
consumer crashes, or simply runs past the timeout, the message
becomes visible again and is redelivered to someone else, so no
message is lost to a crash. This gives at-least-once delivery, and the
phrase carries a warning the module keeps in view: at-least-once
means possibly-more-than-once, because a consumer that is merely slow,
not crashed, can have its message reappear and be processed a second
time while it is still working on the first, so consumers must be
idempotent or the redelivery causes a double effect. The timeout is
the dial: too short and slow consumers cause needless redelivery, too
long and a real crash's message waits that long to be retried. The
module receives a visible message and hides it, deletes a processed
one, and returns lapsed messages to visibility on a tick.
"""

from __future__ import annotations

from beacon.errors import Invalid


class VisibilityQueue:
    def __init__(self, timeout: int) -> None:
        if timeout <= 0:
            raise Invalid(
                "a visibility timeout of zero redelivers a message "
                "the instant it is received"
            )
        self.timeout = timeout
        self.available: list[str] = []
        self.inflight: dict[str, int] = {}

    def send(self, message: str) -> None:
        self.available.append(message)

    def receive(self, now: int) -> str | None:
        self._reclaim(now)
        if not self.available:
            return None
        message = self.available.pop(0)
        self.inflight[message] = now + self.timeout
        return message

    def delete(self, message: str) -> None:
        self.inflight.pop(message, None)

    def _reclaim(self, now: int) -> None:
        lapsed = [
            m for m, visible_at in self.inflight.items() if visible_at <= now
        ]
        for message in lapsed:
            del self.inflight[message]
            self.available.append(message)

    def depth(self, now: int) -> int:
        self._reclaim(now)
        return len(self.available)
