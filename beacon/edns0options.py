"""EDNS options: parse the ones you know, pass the ones you do not, and never choke on either.

The OPT pseudo-record that carries EDNS holds a list of options,
each a numeric code and some data, and the set of codes grows over
time as new capabilities are standardized, cookies, client subnet,
keepalive, name server identifier. A responder therefore faces the
same forward-compatibility demand as unknown record types: it must
handle an option it recognizes and it must not error on one it does
not, because a server that rejected any unfamiliar option would
break every client that adopted a new one before the server was
updated. The rule is to process known options and silently ignore
unknown ones rather than fail, which lets new options roll out
without a flag day. The module classifies each option as known or
unknown, splits a list into the ones a responder acts on and the
ones it leaves alone, and refuses only a genuinely malformed option
with a negative code, since forward compatibility means tolerating
the unfamiliar, not the impossible.
"""

from __future__ import annotations

from beacon.errors import Invalid

KNOWN_OPTIONS = {
    3: "NSID",
    8: "ECS",
    10: "COOKIE",
    11: "KEEPALIVE",
    15: "EDE",
}


def is_known(code: int) -> bool:
    return code in KNOWN_OPTIONS


def process(
    options: list[tuple[int, bytes]],
) -> tuple[list[str], list[int]]:
    handled = []
    ignored = []
    for code, _data in options:
        if code < 0:
            raise Invalid(
                f"option code {code} is negative; forward "
                "compatibility tolerates the unfamiliar, not the "
                "impossible"
            )
        if is_known(code):
            handled.append(KNOWN_OPTIONS[code])
        else:
            ignored.append(code)
    return handled, ignored
