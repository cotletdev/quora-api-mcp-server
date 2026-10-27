"""Everything the server knows about Quora outside `quora/`: names, domains and the session cookie.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "Quora"
SLUG = "quora"
# The command and the prefix of every environment variable (QUORA_AUTH_TOKEN, QUORA_MCP_TOKEN ...).
CLI = "quora-mcp"
ENV = "QUORA"
# Requests may reach only these hosts and their subdomains. Their cookies are read from Chrome,
# Cloudflare's cf_clearance included.
DOMAINS = ("quora.com",)
# The session cookie, the one a pasted token sets. Quora keeps it after sign-out too, so the server asks
# the front page who is signed in (quora/auth.py) instead of trusting the cookie.
SESSION_COOKIES = ("m-b",)
COOKIE_DOMAIN = ".quora.com"
LOGIN_URL = "https://www.quora.com/"
# A final URL with one of these means the app signed the session out. Quora shows its front page signed
# out instead, with no viewer in it (quora/client.py).
LOGGED_OUT_MARKERS: tuple[str, ...] = ()
# An answer with one of these asks you to sign in again before a sensitive action. Quora has none.
RELOGIN_MARKERS: tuple[str, ...] = ()
# Paths of your Quora account that tools may read but never write. Common password, email and sign-in
# paths are refused for every app (core/account_guard.py); Quora adds none.
ACCOUNT_PATHS: tuple[str, ...] = ()
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/quora"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = (
    "Start with get_my_profile to see the account, then search_questions or list_answer_requests "
    "to find questions to answer."
)
