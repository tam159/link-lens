"""Signing in to the console: who is asking, and in which role.

`authenticate` tries each resolver in turn, as the product service does for API
keys. One exists today: tokens listed in `LINK_LENS_ADMIN_USERS`, for
development and for one machine. An identity provider is one more resolver
that returns the same `Principal`; no route changes when it is added.

Roles are checked here, in the API, never in the pages. Each role includes the
one before it:

    engineer        reads sources, releases, ontology versions and what needs attention
    product_owner   also searches the catalogue, previews and adds sources, sets
                    cadence and pauses, previews and records releases
    admin           also manages clients, tiers and keys, and reads the audit log
"""

import hmac
import json
import logging
from dataclasses import dataclass

from .. import logs
from ..settings import settings

ROLES = ("engineer", "product_owner", "admin")
COOKIE = "ll_console"
# A request signed in by cookie must carry this header to change anything, so
# another site cannot make the browser act for the person.
CONSOLE_HEADER = "x-linklens-console"


@dataclass(frozen=True)
class Principal:
    name: str
    role: str

    def may(self, role):
        return ROLES.index(self.role) >= ROLES.index(role)


def people():
    """Who `LINK_LENS_ADMIN_USERS` lists, by token. Anything unreadable lists nobody."""
    try:
        listed = json.loads(settings().admin_users or "{}")
    except ValueError:
        logs.event("console.users_unreadable", level=logging.WARNING)
        return {}
    return listed if isinstance(listed, dict) else {}


def development_token(token):
    """A person listed in `LINK_LENS_ADMIN_USERS`, by the token they hold."""
    found = None
    for known, person in people().items():
        # Compare every entry, in constant time, whichever one matches.
        if hmac.compare_digest(known.encode(), token.encode()):
            found = person
    if (
        not isinstance(found, dict)
        or found.get("role") not in ROLES
        or not str(found.get("name") or "").strip()
    ):
        return None
    return Principal(str(found["name"]).strip(), found["role"])


RESOLVERS = [development_token]


def authenticate(token):
    """The person a token belongs to, or None."""
    if not token:
        return None
    for resolve in RESOLVERS:
        principal = resolve(token)
        if principal is not None:
            return principal
    return None
