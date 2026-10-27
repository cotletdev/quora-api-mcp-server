"""List my answers: `UserProfileAnswersMostRecent_RecentAnswers_Query` for the viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.helpers import limit
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import answer_row

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "limit": {"type": "integer", "description": "1 to 50. Default: 20."},
        "cursor": {"type": "string", "description": "Next page cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}


@tool(
    name="list_my_answers",
    title="List my answers",
    access="read",
    description="Your answers with question, text, URL and views, newest first.",
    details=(
        "Lists the answers on your profile, newest first (pinned ones may come first), with the question each "
        "answers, the answer text and URL, upvotes and views. Pass next_cursor back as cursor for the next page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /answers",
    example_response={
        "answers": [
            {
                "answer_id": "391847562",
                "author": "Jordan Lee",
                "author_url": "https://www.quora.com/profile/Jordan-Lee",
                "text": "Most of it is the roads...",
                "url": "https://www.quora.com/Why-is-gravel-cycling-growing-in-popularity/answer/Jordan-Lee",
                "upvotes": 3,
                "views": 120,
                "comments": 0,
                "shares": 0,
                "created_at": "2026-10-27T14:20:00Z",
                "question": "Why is gravel cycling growing in popularity?",
                "question_url": "https://www.quora.com/Why-is-gravel-cycling-growing-in-popularity",
            }
        ],
        "next_cursor": None,
    },
)
async def list_my_answers(ctx: ToolContext, args: dict[str, Any]) -> Any:
    state = await session(ctx)
    variables = {
        "uid": state.viewer_uid,
        "first": limit(args, 20, 50),
        "after": args.get("cursor") or None,
        "answerFilterTid": None,
    }
    data = await graphql(ctx, state, "UserProfileAnswersMostRecent_RecentAnswers_Query", variables)
    connection = (data.get("user") or {}).get("recentPublicAndPinnedAnswersConnection") or {}
    answers = [
        answer_row(edge["node"], with_question=True)
        for edge in connection.get("edges") or []
        if isinstance((edge or {}).get("node"), dict) and edge["node"].get("aid")
    ]
    page = connection.get("pageInfo") or {}
    return {"answers": answers, "next_cursor": page.get("endCursor") if page.get("hasNextPage") else None}
