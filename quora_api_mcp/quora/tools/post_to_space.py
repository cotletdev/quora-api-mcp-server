"""Post to Space: `UniversalComposerModalWrapper_postAdd_Mutation`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import rich_text, space_id

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "space_id": {"type": "string", "description": "Space ID from list_my_spaces."},
        "body_markdown": {
            "type": "string",
            "description": "Post text. Plain: a blank line starts a paragraph, no formatting or images.",
        },
        "title": {"type": "string", "description": "Optional post title."},
        "mode": {"type": "string", "enum": ["post", "queue"], "description": "post or queue. Default: post."},
    },
    "required": ["space_id", "body_markdown"],
    "additionalProperties": False,
}


@tool(
    name="post_to_space",
    title="Post to Space",
    access="write",
    confirm=True,
    description="New post in a Space you contribute to, posted now or added to its queue.",
    details=(
        "Creates a post under your name in a Space. As an admin, moderator or contributor, mode post publishes it "
        "at once and its followers see it; mode queue adds it to the Space queue, which posts it later. In a "
        "Space where you only follow, Quora sends it to the admins for review (status submitted). By default you "
        "confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /spaces/{space_id}/posts",
    example_response={"post_id": "258040991", "space_id": "7310452", "status": "published"},
)
async def post_to_space(ctx: ToolContext, args: dict[str, Any]) -> Any:
    tribe_id = space_id(args)
    body = str(args["body_markdown"]).strip()
    if not body:
        raise ToolError("body_markdown must not be empty.", ErrorCode.INVALID_INPUT)
    mode = str(args.get("mode") or "post")
    if mode not in {"post", "queue"}:
        raise ToolError("mode must be post or queue.", ErrorCode.INVALID_INPUT)
    state = await session(ctx)
    variables = {
        "tribeId": tribe_id,
        "title": rich_text(str(args.get("title") or "")),
        "content": rich_text(body),
        "shouldQueue": mode == "queue",
        "accessOption": None,
        "credentialId": None,
        "captcha": None,
    }
    data = await graphql(ctx, state, "UniversalComposerModalWrapper_postAdd_Mutation", variables, write=True)
    added = data.get("postAdd") or {}
    if not added.get("success"):
        reason = added.get("failureType") or added.get("status")
        message = f"Quora did not publish the post ({reason})." if reason else "Quora did not publish the post."
        raise ToolError(message, ErrorCode.TARGET_ERROR)
    post = added.get("post") or {}
    if added.get("queueItem"):
        status = "queued"
    elif added.get("submission"):
        status = "submitted"
    else:
        status = "published"
    return {
        "post_id": str(post["pid"]) if post.get("pid") else None,
        "space_id": str(tribe_id),
        "status": status,
    }
