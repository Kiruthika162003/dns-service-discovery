"""The truncated bit: an incomplete UDP answer is a summons to TCP, not a partial answer to use.

When a DNS answer will not fit the negotiated UDP size, the server
does not send a partial RRset and hope, it sends what it can with
the truncated bit set, which is a specific instruction: this answer
is incomplete, ask again over TCP where there is no size limit. A
client that treated the truncated records as the answer would act on
a fraction of an RRset, choosing among some of a name's addresses
while blind to the rest, or worse missing the records that change
the meaning, so the only correct response to the truncated bit is to
discard the partial answer and retry the whole query over TCP. There
is a symmetry that catches a bug: the truncated bit should never
appear on a TCP response, because TCP has no length ceiling to
truncate against, so a truncated answer arriving over TCP is not a
summons the client can obey, it is a sign something is malformed
upstream. The module decides the client's action from the truncated
bit and the transport, returning use-answer, retry-over-tcp, and
refusing the impossible truncation-over-TCP as the error it is.
"""

from __future__ import annotations

from beacon.errors import Invalid


def client_action(truncated: bool, over_tcp: bool) -> str:
    if not truncated:
        return "use-answer"
    if over_tcp:
        raise Invalid(
            "the truncated bit is set on a TCP response, which has "
            "no size limit to truncate against; this is malformed, "
            "not a summons the client can obey"
        )
    return "retry-over-tcp"
