"""The TCP connection state machine: the handshake, the close, and why TIME_WAIT lingers.

A TCP connection is a state machine, and getting the transitions
right is what makes the protocol reliable across an unreliable
network. It opens with the three-way handshake: an active opener
sends SYN and enters SYN_SENT, the passive side in LISTEN replies
SYN-ACK and enters SYN_RECEIVED, and the final ACK moves both to
ESTABLISHED. It closes with a four-way exchange, each side sending a
FIN and acknowledging the other's, passing through FIN_WAIT and
CLOSE_WAIT states, because either side may stop sending
independently. The state that puzzles operators is TIME_WAIT, which
the side that closed actively sits in for twice the maximum segment
lifetime before finally releasing the connection. It waits that long
on purpose: a delayed duplicate segment from the just-closed
connection could otherwise arrive during a new connection reusing the
same port pair and be mistaken for its data, so TIME_WAIT holds the
four-tuple quarantined until any such straggler must have expired,
which is why a busy server accumulates many TIME_WAIT sockets, a real
and famous resource cost. The module maps a state and an event to the
next state, refusing an event that has no defined transition from the
current state as the protocol violation it is.
"""

from __future__ import annotations

from beacon.errors import Invalid

_TRANSITIONS = {
    ("CLOSED", "active-open"): "SYN_SENT",
    ("CLOSED", "passive-open"): "LISTEN",
    ("LISTEN", "recv-syn"): "SYN_RECEIVED",
    ("SYN_SENT", "recv-syn-ack"): "ESTABLISHED",
    ("SYN_RECEIVED", "recv-ack"): "ESTABLISHED",
    ("ESTABLISHED", "close"): "FIN_WAIT_1",
    ("ESTABLISHED", "recv-fin"): "CLOSE_WAIT",
    ("FIN_WAIT_1", "recv-ack"): "FIN_WAIT_2",
    ("FIN_WAIT_2", "recv-fin"): "TIME_WAIT",
    ("CLOSE_WAIT", "close"): "LAST_ACK",
    ("LAST_ACK", "recv-ack"): "CLOSED",
    ("TIME_WAIT", "timeout"): "CLOSED",
}


def transition(state: str, event: str) -> str:
    key = (state, event)
    if key not in _TRANSITIONS:
        raise Invalid(
            f"no transition from {state} on {event}; the event is a "
            "protocol violation in this state, not a state change"
        )
    return _TRANSITIONS[key]


def lingers_in_time_wait(state: str) -> bool:
    return state == "TIME_WAIT"
