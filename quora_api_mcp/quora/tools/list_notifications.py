"""List notifications: `NotifsPagedListWrapperQuery`, next pages `NotifsPagedList_LoadSentNotifCollection_Query`.
Reading does not clear the badge: the page's clear mutation is not sent."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.helpers import limit
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, iso, plain_text, user_name

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "limit": {"type": "integer", "description": "1 to 50. Default: 20."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}


def _row(node: dict[str, Any]) -> dict[str, Any]:
    question = node.get("targetQuestion") if isinstance(node.get("targetQuestion"), dict) else None
    return {
        "notification_id": str(node.get("sncid")),
        "title": node.get("translatedTitle"),
        "body": plain_text(node.get("translatedBody")) or None,
        "context": node.get("translatedContext"),
        "from": user_name(node.get("responsibleUser")),
        "url": absolute(node.get("clickthroughUrl")),
        "question": plain_text(question.get("title")) if question else None,
        "read": bool(node.get("isRead")),
        "updated_at": iso(node.get("updatedTime")),
    }


@tool(
    name="list_notifications",
    title="List notifications",
    access="read",
    description="Your Quora notifications, newest first: answers, upvotes, follows, Space invites.",
    details=(
        "Lists the notifications of the signed-in account, newest first, with what happened, who did it and the "
        "link. Reading them here does not mark them read or clear the badge on Quora. Pass next_cursor back as "
        "cursor for the next page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /notifications",
    example_response={
        "notifications": [
            {
                "notification_id": "78148856888",
                "title": "Quora invited you to follow Quora Product Updates",
                "body": None,
                "context": "Quora Product Updates",
                "from": "Quora",
                "url": "https://productupdates.quora.com",
                "question": None,
                "read": False,
                "updated_at": "2026-10-27T11:30:41Z",
            }
        ],
        "unread_badge": 1,
        "next_cursor": None,
    },
)
async def list_notifications(ctx: ToolContext, args: dict[str, Any]) -> Any:
    count = limit(args, 20, 50)
    cursor = str(args.get("cursor") or "")
    state = await session(ctx)
    base = {"first": count, "filterCategory": None, "filterTribeId": None}
    if cursor:
        after, _, updated = cursor.partition(":")
        if not updated.isdigit():
            raise ToolError("cursor must be the next_cursor value from the previous call.", ErrorCode.INVALID_INPUT)
        variables = {**base, "after": after, "updateTime": int(updated)}
        data = await graphql(ctx, state, "NotifsPagedList_LoadSentNotifCollection_Query", variables)
    else:
        data = await graphql(ctx, state, "NotifsPagedListWrapperQuery", base)
    viewer = data.get("viewer") or {}
    connection = viewer.get("sentNotifCollectionsConnection") or {}
    nodes = [edge["node"] for edge in connection.get("edges") or [] if isinstance((edge or {}).get("node"), dict)]
    page = connection.get("pageInfo") or {}
    next_cursor = None
    if page.get("hasNextPage") and nodes and page.get("endCursor") is not None:
        next_cursor = f"{page['endCursor']}:{nodes[-1].get('updatedTime')}"
    return {
        "notifications": [_row(node) for node in nodes],
        "unread_badge": viewer.get("notificationNavBadgeCount"),
        "next_cursor": next_cursor,
    }
