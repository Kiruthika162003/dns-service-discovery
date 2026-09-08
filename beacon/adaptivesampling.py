"""Adaptive trace sampling: keep every error and slow request, sample the boring rest.

Recording a trace for every request at scale is unaffordable, but
sampling uniformly at a low rate throws away the traces that matter
most, since errors and slow requests are rare and a low uniform rate
almost never captures them, leaving the boring fast successes
over-represented and the interesting failures invisible. Adaptive,
tail-aware sampling inverts that. It keeps every trace that is
interesting on its face, any error, any request slower than a
latency threshold, so the rare and important are captured with
certainty, and it samples the remaining ordinary traffic at a low
probability just to keep a representative baseline. The result is a
trace store dense in the failures an operator actually investigates
and sparse in the successes they do not, at a fraction of the volume
of keeping everything. The judgement it encodes is that value is not
uniform across requests, so the sampling rate should not be either.
The module decides whether to keep a trace from its error flag, its
latency against the slow threshold, and a probability draw for the
rest, and reports the effective keep rate over a batch so the volume
saved is a measured number, not a hope.
"""

from __future__ import annotations

from beacon.errors import Invalid


class AdaptiveSampler:
    def __init__(self, slow_threshold_ms: int, base_rate: float) -> None:
        if slow_threshold_ms < 0:
            raise Invalid("a slow threshold is never negative")
        if not 0.0 <= base_rate <= 1.0:
            raise Invalid(
                f"the base sample rate {base_rate} is not a "
                "probability between zero and one"
            )
        self.slow_threshold_ms = slow_threshold_ms
        self.base_rate = base_rate

    def keep(self, is_error: bool, latency_ms: int, draw: float) -> bool:
        if not 0.0 <= draw < 1.0:
            raise Invalid("the draw must be in [0, 1)")
        if is_error:
            return True
        if latency_ms >= self.slow_threshold_ms:
            return True
        return draw < self.base_rate

    def is_interesting(self, is_error: bool, latency_ms: int) -> bool:
        return is_error or latency_ms >= self.slow_threshold_ms

    def keep_rate(
        self, traces: list[tuple[bool, int, float]]
    ) -> float:
        if not traces:
            raise Invalid("no traces to measure a keep rate over")
        kept = sum(
            1
            for is_error, latency, draw in traces
            if self.keep(is_error, latency, draw)
        )
        return kept / len(traces)
