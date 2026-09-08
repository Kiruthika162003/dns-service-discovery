"""Trace context propagation: thread a request's spans into one trace across every service.

A request that fans out across services produces a span at each hop,
and to assemble them into a single trace the services must agree on
an identifier and pass it along. The W3C traceparent header carries
it: a version, a trace id shared by every span of the request, the
span id of the immediate parent, and flags whose low bit says whether
the trace is sampled. Propagation has two rules the module enforces.
The trace id must be carried unchanged through every hop, since it is
what stitches the spans together, and each service creates a new span
id for its own work while recording the received span id as its
parent, which is how the tree of spans is built. The sampled flag is
the subtle one: it must be propagated exactly as received, because
sampling is a decision made once at the root and every service must
honor it, so a service that re-decided sampling per hop would produce
a trace that is present at some services and absent at others, a
broken partial trace worse than none. The module parses a traceparent
into its fields, reports whether it is sampled, and builds a child
context that keeps the trace id and sampled flag while advancing the
span, refusing a malformed header rather than guessing its parts.
"""

from __future__ import annotations

from beacon.errors import Invalid


def parse(traceparent: str) -> tuple[str, str, str]:
    parts = traceparent.split("-")
    if len(parts) != 4:
        raise Invalid(
            "a traceparent has four dash-separated fields; a "
            "malformed header cannot be guessed into a trace"
        )
    _version, trace_id, span_id, flags = parts
    if len(trace_id) != 32 or len(span_id) != 16 or len(flags) != 2:
        raise Invalid(
            "the traceparent fields are the wrong width; the trace "
            "id is 32 hex, the span id 16, the flags 2"
        )
    if trace_id == "0" * 32 or span_id == "0" * 16:
        raise Invalid(
            "an all-zero trace or span id is invalid; it names no "
            "trace to join"
        )
    return trace_id, span_id, flags


def is_sampled(flags: str) -> bool:
    return int(flags, 16) & 0x01 == 1


def child(traceparent: str, new_span_id: str) -> str:
    trace_id, _parent_span, flags = parse(traceparent)
    if len(new_span_id) != 16:
        raise Invalid("a span id is 16 hex characters")
    return f"00-{trace_id}-{new_span_id}-{flags}"
