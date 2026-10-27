"""Search questions: `SearchResultsListQuery` with `resultType` question."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.helpers import limit
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import question_row

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search words."},
        "limit": {"type": "integer", "description": "1 to 50. Default: 20."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": ["query"],
    "additionalProperties": False,
}


@tool(
    name="search_questions",
    title="Search questions",
    access="read",
    description="Questions matching a keyword, with answer counts.",
    details=(
        "Searches Quora for questions matching your words and returns them in the order Quora shows them, with "
        "the number of answers each has. Use question_url from an item with get_question. Pass next_cursor back "
        "as cursor for more."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /questions/search",
    example_response={
        "questions": [
            {
                "question_id": "44880608",
                "question": "Why is gravel cycling growing in popularity?",
                "question_url": "https://www.quora.com/Why-is-gravel-cycling-growing-in-popularity",
                "answers": 6,
                "followers": 2,
                "locked": False,
            }
        ],
        "next_cursor": "19",
    },
)
async def search_questions(ctx: ToolContext, args: dict[str, Any]) -> Any:
    query = str(args["query"]).strip()
    if not query:
        raise ToolError("query must not be empty.", ErrorCode.INVALID_INPUT)
    state = await session(ctx)
    variables = {
        "query": query,
        "disableSpellCheck": None,
        "resultType": "question",
        "author": None,
        "time": "all_times",
        "first": limit(args, 20, 50),
        "after": str(args.get("cursor") or "-1"),
        "tribeId": None,
        "sortOrder": "relevance",
        "tid": None,
    }
    data = await graphql(ctx, state, "SearchResultsListQuery", variables)
    connection = data.get("searchConnection") or {}
    questions = [
        question_row(edge["node"]["question"])
        for edge in connection.get("edges") or []
        if isinstance(edge, dict) and isinstance((edge.get("node") or {}).get("question"), dict)
    ]
    page = connection.get("pageInfo") or {}
    return {"questions": questions, "next_cursor": page.get("endCursor") if page.get("hasNextPage") else None}
