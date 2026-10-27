"""Who is signed in: the viewer in the HTML of the front page, for "Signed in as ..."."""

from __future__ import annotations

from typing import TYPE_CHECKING

from quora_api_mcp.core.errors import AuthExpiredError
from quora_api_mcp.quora.client import page_state

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext


async def whoami(ctx: ToolContext) -> str | None:
    """None only when Quora says signed out; any other failure raises (detection tries again later)."""
    try:
        state = await page_state(ctx)
    except AuthExpiredError:
        return None
    if state is None:
        return None
    return state.name or f"Quora user {state.viewer_uid}"
