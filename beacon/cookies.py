"""DNS cookies: a cheap handshake that turns off-path attackers away.

An off-path attacker cannot see the traffic, so forging a
response means guessing the query's identifiers; DNS cookies
raise the guessing cost with a shared secret the client sends
and the server echoes. The client cookie is a nonce the
server cannot predict, the server cookie is a MAC the client
cannot forge, and a response bearing the wrong cookie is
discarded before its records are even read, which stops the
off-path forgery cold because the attacker never saw the
cookie to echo it. The subtlety this module keeps honest is
the bootstrap: a client with no server cookie yet must be
allowed to ask, so first contact is cookie-optional and only
subsequent queries are cookie-required, and a server that
demanded cookies from the very first packet would lock out
every new client, trading an off-path defense for an
on-by-default outage. On-path attackers see the cookie and
are unbothered, which the module states plainly rather than
overselling the defense.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from beacon.errors import Invalid


def _server_cookie(client_cookie: str, secret: str) -> str:
    return hashlib.sha256(
        f"{client_cookie}|{secret}".encode()
    ).hexdigest()[:16]


@dataclass
class CookieServer:
    secret: str
    known_clients: set[str] = field(default_factory=set)
    forgeries_dropped: int = 0
    bootstraps: int = 0

    def respond(
        self,
        client_cookie: str,
        server_cookie: str | None,
    ) -> str:
        if not client_cookie:
            raise Invalid(
                "a query with no client cookie cannot be "
                "protected; the nonce is the whole handshake"
            )
        expected = _server_cookie(client_cookie, self.secret)
        if server_cookie is None:
            if client_cookie in self.known_clients:
                raise Invalid(
                    f"{client_cookie} was issued a server "
                    "cookie already; dropping it now is a "
                    "downgrade an on-path attacker would love"
                )
            self.known_clients.add(client_cookie)
            self.bootstraps += 1
            return (
                f"first contact: issuing server cookie "
                f"{expected}; bootstrap is cookie-optional so "
                "new clients are not locked out"
            )
        if server_cookie != expected:
            self.forgeries_dropped += 1
            raise Invalid(
                "server cookie mismatch: discarded before the "
                "records are read, because the off-path "
                "attacker never saw the cookie to echo it"
            )
        return (
            f"{client_cookie}: cookie verified, answer served"
        )

    def on_path_note(self) -> str:
        return (
            "an on-path attacker sees the cookie and echoes "
            "it; cookies raise the off-path cost and this "
            "module says so instead of overselling"
        )

    def ledger(self) -> str:
        return (
            f"{self.bootstraps} bootstrap(s), "
            f"{len(self.known_clients)} known client(s), "
            f"{self.forgeries_dropped} off-path forgery(ies) "
            "dropped before their records were read"
        )
