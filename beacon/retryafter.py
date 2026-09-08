"""Retry-After: turn a rate-limit rejection into a cooperative backoff instead of a retry storm.

When a server rate-limits a client and rejects a request, how it
rejects matters as much as that it rejects. A bare rejection tells
the client only that it failed, so the client retries blindly, often
immediately, and a crowd of rejected clients hammering the limited
endpoint turns the limit into an amplifier of load rather than a
shield against it. The Retry-After response, the 429 with a wait
time, makes the rejection cooperative: the server computes when the
client's allowance will next permit a request, from how far the token
bucket is below one token and how fast it refills, and tells the
client exactly how long to wait, so a well-behaved client returns at
the right moment and not before. The effect is that the limit sheds
load smoothly, spreading the rejected clients out over time rather
than concentrating their retries into a storm. The honest dependency
is client cooperation, since a client is free to ignore the header,
but for the well-behaved majority it converts thundering retries into
paced ones. The module computes the wait until the next token from a
token count and refill rate, and returns the status and wait for a
request, allowed or rate-limited.
"""

from __future__ import annotations

from math import ceil

from beacon.errors import Invalid


def retry_after(tokens: float, refill_rate: float) -> int:
    if refill_rate <= 0:
        raise Invalid(
            "a non-positive refill rate never grants a token, so there "
            "is no finite time to retry after"
        )
    if tokens >= 1:
        return 0
    return ceil((1 - tokens) / refill_rate)


def response(
    tokens: float, refill_rate: float
) -> tuple[int, int]:
    if tokens >= 1:
        return (200, 0)
    return (429, retry_after(tokens, refill_rate))
