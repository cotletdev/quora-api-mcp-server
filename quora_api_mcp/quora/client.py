"""Quora web client on www.quora.com, recorded on a test account (27.10.2026).

The session is the `m-b` cookie family. Reads go to `POST /graphql/gql_para_POST?q=<Name>`, writes to
`/graphql/gql_POST?q=<Name>`, with a persisted-query body `{queryName, variables, extensions: {hash}}` and
headers the page builds from `window.ansFrontendGlobals`: the values sit in the HTML of `GET /`. One fetch of
that page gives all of them, so `page_state` is the single source.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.quora.operations import READS, WRITES

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

WEB = "https://www.quora.com"
GRAPHQL = f"{WEB}/graphql"
_BOUNDARY = "--qgqlmpb"
_HTML = {"accept": "text/html,application/xhtml+xml", "upgrade-insecure-requests": "1"}


@dataclass(frozen=True)
class PageState:
    """What the front page tells a GraphQL call: identity headers and the viewer."""

    formkey: str
    revision: str
    canary: bool
    broadcast_id: str
    window_id: str
    page_creation_time: str
    viewer_uid: int
    name: str | None

    def headers(self) -> dict[str, str]:
        return {
            "quora-formkey": self.formkey,
            "quora-broadcast-id": self.broadcast_id,
            "quora-revision": self.revision,
            "quora-canary-revision": "true" if self.canary else "false",
            "quora-window-id": self.window_id,
            "quora-page-creation-time": self.page_creation_time,
            "content-type": "application/json",
            "origin": WEB,
            "referer": f"{WEB}/",
        }


def _find(html: str, pattern: str) -> str | None:
    match = re.search(pattern, html)
    return match.group(1) if match else None


def _viewer_name(html: str, uid: int) -> str | None:
    """The viewer's name from the escaped feed JSON: the UserName node whose id is base64 `UserName:{uid}:LATN`."""
    node = base64.b64encode(f"UserName:{uid}:LATN".encode()).decode()
    tail = r'\\*",\\*"reverseOrder\\*":false,\\*"givenName\\*":\\*"(.*?)\\*",\\*"familyName\\*":\\*"(.*?)\\*"'
    match = re.search(re.escape(node) + tail, html)
    if match is None:
        return None
    return " ".join(part for part in (match.group(1), match.group(2)) if part) or None


def parse_page(html: str) -> PageState | None:
    """None when the page is not a Quora page signed in (no `viewerMemberUid`, or 0): signed out or a challenge."""
    uid = _find(html, r'"viewerMemberUid": (\d+)')
    if uid is None or int(uid) == 0:
        return None
    return _state(html, int(uid))


def signed_out_headers(html: str) -> dict[str, str] | None:
    """The identity headers of a signed-out front page (sign-up and sign-in GraphQL); None for a challenge."""
    if _find(html, r'"formkey": "([0-9a-f]+)"') is None:
        return None
    return _state(html, 0).headers()


def _state(html: str, uid: int) -> PageState:
    formkey = _find(html, r'"formkey": "([0-9a-f]+)"')
    revision = _find(html, r'"revision": "([0-9a-f]+)"')
    broadcast = _find(html, r'"broadcastId": "([^"]+)"')
    window = _find(html, r'"windowId": "([^"]+)"')
    created = _find(html, r'"pageCreationTime": (\d+)')
    if not (formkey and revision and broadcast and window and created):
        raise ToolError("Quora front page changed: no formkey or revision in it.", ErrorCode.TARGET_ERROR)
    return PageState(
        formkey=formkey,
        revision=revision,
        canary=_find(html, r'"isCanaryRevision": (true|false)') == "true",
        broadcast_id=broadcast,
        window_id=window,
        page_creation_time=created,
        viewer_uid=uid,
        name=_viewer_name(html, uid) if uid else None,
    )


async def page_state(ctx: ToolContext) -> PageState | None:
    """Fetch `GET /` and read it; None when signed out. A Cloudflare challenge or 403 reaches `ctx.call` as a block."""
    response = await ctx.call("GET", f"{WEB}/", headers=_HTML)
    if response.status != 200:
        raise ToolError(f"Quora answered {response.status} to the front page.", ErrorCode.TARGET_ERROR)
    return parse_page(response.text)


async def request_headers(ctx: ToolContext) -> dict[str, str]:
    """The identity headers of a GraphQL call, read from the front page now (for a request sent by hand)."""
    state = await page_state(ctx)
    if state is None:
        raise ToolError("Quora is signed out.", ErrorCode.AUTH_EXPIRED)
    return state.headers()


async def session(ctx: ToolContext) -> PageState:
    """The front page read once per tool run: every GraphQL call of the run reuses its headers."""
    state = await page_state(ctx)
    if state is None:
        raise ToolError("Quora is signed out.", ErrorCode.AUTH_EXPIRED)
    return state


def _parts(text: str) -> list[dict[str, Any]]:
    """The JSON parts of a `multipart/mixed` answer (boundary `--qgqlmpb`), or the one JSON body."""
    if not text.lstrip().startswith("--"):
        try:
            return [json.loads(text)]
        except ValueError as exc:
            raise ToolError("Quora answered with something that is not JSON.", ErrorCode.TARGET_ERROR) from exc
    parts: list[dict[str, Any]] = []
    for chunk in text.split(_BOUNDARY):
        start, end = chunk.find("{"), chunk.rfind("}")
        if start < 0 or end < start:
            continue
        try:
            parts.append(json.loads(chunk[start : end + 1]))
        except ValueError:
            continue
    return parts


def _merge(root: dict[str, Any], part: dict[str, Any]) -> None:
    """Relay incremental delivery: a part with `path` is a streamed list item (last step a number) or a
    deferred fragment merged into the object at that path."""
    data = part.get("data")
    path = part.get("path")
    if not isinstance(data, dict):
        return
    if not path:
        for key, value in data.items():
            root.setdefault(key, value)
        return
    target: Any = root
    for step in path[:-1]:
        if isinstance(target, list) and isinstance(step, int) and step < len(target):
            target = target[step]
        elif isinstance(target, dict):
            target = target.get(step)
        else:
            return
        if target is None:
            return
    last = path[-1]
    if isinstance(last, int) and isinstance(target, list):
        while len(target) <= last:
            target.append(None)
        target[last] = data
        return
    holder = target[last] if isinstance(target, dict) and isinstance(target.get(last), dict) else None
    if holder is None and isinstance(target, dict):
        holder = target.setdefault(last, {})
    if isinstance(holder, dict):
        holder.update(data)


async def graphql(
    ctx: ToolContext, state: PageState, name: str, variables: dict[str, Any], *, write: bool = False
) -> dict[str, Any]:
    """`data` of one persisted operation (operations.py). An answer with errors and no data, the 200
    "Server Error" Quora gives for a bad id or a missing variable as well, is a target error."""
    hashes = WRITES if write else READS
    endpoint = "gql_POST" if write else "gql_para_POST"
    body = {"queryName": name, "variables": variables, "extensions": {"hash": hashes[name]}}
    response = await ctx.call("POST", f"{GRAPHQL}/{endpoint}?q={name}", json=body, headers=state.headers())
    if response.status >= 400:
        raise ToolError(f"Quora answered {response.status}.", ErrorCode.TARGET_ERROR)
    parts = _parts(response.text)
    data: dict[str, Any] = {}
    errors: list[Any] = []
    for part in parts:
        errors.extend(part.get("errors") or [])
        _merge(data, part)
    if errors and not any(value is not None for value in data.values()):
        raise ToolError("Quora refused the request. Check the IDs and URL you gave.", ErrorCode.TARGET_ERROR)
    return data
