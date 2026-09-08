"""A dead-letter queue: after enough failed deliveries, set a poison message aside.

A message that cannot be processed, malformed, referencing something
gone, triggering a bug, will fail every time it is delivered, and a
queue that simply retries it forever has two bad outcomes: the
message loops endlessly consuming resources, and worse, if the queue
preserves order it blocks every message behind it, a single poison
message stalling the whole flow, head-of-line blocking. A dead-letter
queue breaks the loop. Each message's delivery attempts are counted,
and once the count reaches a maximum the message is moved out of the
main queue into a dead-letter queue, where it stops being retried and
waits for separate handling, a human, an alert, an out-of-band
repair. The main queue flows again, and the unprocessable message is
neither lost nor allowed to jam everything, it is set aside. The
tradeoff is that dead-lettered messages need attention they will not
get automatically, so a dead-letter queue that no one watches is a
silent hole where failures accumulate. The module counts delivery
attempts per message, decides retry versus dead-letter against the
maximum, and reports the dead-lettered set, so the poison messages
are collected rather than looping.
"""

from __future__ import annotations

from beacon.errors import Invalid


class DeliveryTracker:
    def __init__(self, max_attempts: int) -> None:
        if max_attempts < 1:
            raise Invalid(
                "a maximum of zero attempts never delivers a message "
                "even once; that is a closed queue"
            )
        self.max_attempts = max_attempts
        self.attempts: dict[str, int] = {}
        self.dead_letters: set[str] = set()

    def attempt(self, message: str) -> str:
        self.attempts[message] = self.attempts.get(message, 0) + 1
        if self.attempts[message] >= self.max_attempts:
            self.dead_letters.add(message)
            return "dead-letter"
        return "retry"

    def is_dead_lettered(self, message: str) -> bool:
        return message in self.dead_letters

    def attempt_count(self, message: str) -> int:
        return self.attempts.get(message, 0)
