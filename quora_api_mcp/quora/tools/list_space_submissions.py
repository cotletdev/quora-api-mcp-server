"""List Space submissions: `TribeContentSourcesModalQuery` (inbox header) and `SubmissionsMultifeedQuery`.

The story shape of a submission was not seen yet (no second account submitted), so each `submission` object is
found by its `submissionId` anywhere in the feed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.helpers import limit
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, find_all, iso, plain_text, space_id, user_name

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "space_id": {"type": "string", "description": "Space ID from list_my_spaces."},
        "limit": {"type": "integer", "description": "1 to 50. Default: 20."},
    },
    "required": ["space_id"],
    "additionalProperties": False,
}

FEED = "admin_tribe_submissions_ranked"


def _row(submission: dict[str, Any]) -> dict[str, Any]:
    content = submission.get("contentObject") or {}
    for key in ("answer", "post", "question", "tribeQuestion"):
        if not content and isinstance(submission.get(key), dict):
            content = submission[key]
    question = content.get("question") if isinstance(content.get("question"), dict) else None
    author = content.get("author") or content.get("asker") or submission.get("author") or submission.get("creator")
    title = plain_text(content.get("title")) or (plain_text(question.get("title")) if question else "")
    return {
        "submission_id": str(submission["submissionId"]),
        "type": (content.get("__typename") or "").lower() or None,
        "title": title or None,
        "text": plain_text(content.get("content")) or None,
        "url": absolute(content.get("permaUrl") or content.get("url")),
        "author": user_name(author),
        "submitted_at": iso(submission.get("creationTime") or content.get("creationTime")),
    }


@tool(
    name="list_space_submissions",
    title="List Space submissions",
    access="read",
    description="Answers, posts and questions followers submitted to your Space, waiting for review.",
    details=(
        "Lists the submissions in the Space inbox: answers, posts and questions followers sent for "
        "consideration. Admins and moderators only. A Space gets submissions only when its settings allow them; "
        "submissions_enabled says whether this one does. Pass submission_id to review_space_submission."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /spaces/{space_id}/submissions",
    example_response={
        "space_id": "7310452",
        "submissions_enabled": True,
        "review_period_days": 14,
        "pending": 1,
        "submissions": [
            {
                "submission_id": "88412",
                "type": "post",
                "title": "Grind size for a light roast",
                "text": "After a month of dialing in light roasts...",
                "url": "https://homeespressonotes.quora.com/Grind-size-for-a-light-roast",
                "author": "Ana Lopez",
                "submitted_at": "2026-10-09T10:30:00Z",
            }
        ],
    },
)
async def list_space_submissions(ctx: ToolContext, args: dict[str, Any]) -> Any:
    tribe_id = space_id(args)
    state = await session(ctx)
    header = await graphql(
        ctx, state, "TribeContentSourcesModalQuery", {"tribeId": tribe_id, "tribeFeedType": FEED, "sncid": 0}
    )
    tribe = header.get("tribe") or {}
    if not tribe.get("viewerCanManageSubmissions"):
        raise ToolError("Only admins and moderators of this Space see its submissions.", ErrorCode.TARGET_ERROR)
    variables = {
        "tribeId": tribe_id,
        "tribeFeedType": FEED,
        "first": limit(args, 20, 50),
        "multifeedAfter": None,
        "multifeedNumBundlesOnClient": 0,
        "injectionType": None,
        "injectionData": None,
    }
    feed = await graphql(ctx, state, "SubmissionsMultifeedQuery", variables)
    seen: set[str] = set()
    submissions = []
    for submission in find_all(feed.get("multifeedObject"), "submissionId"):
        key = str(submission["submissionId"])
        if key not in seen:
            seen.add(key)
            submissions.append(_row(submission))
    settings = tribe.get("settings") or {}
    return {
        "space_id": str(tribe_id),
        "submissions_enabled": bool(settings.get("allowSubmissions")),
        "review_period_days": settings.get("submissionReviewPeriod"),
        "pending": tribe.get("valueAll"),
        "submissions": submissions,
    }
