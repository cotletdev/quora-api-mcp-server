"""Get question: `QuestionPageLoadablePreviewQuery` by slug, then `QuestionPagedListPaginationQuery`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, answer_row, bounded, plain_text, question_slug

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question_url": {"type": "string", "description": "Question URL on quora.com."},
        "answers_limit": {"type": "integer", "description": "0 to 20. Default: 5."},
    },
    "required": ["question_url"],
    "additionalProperties": False,
}


@tool(
    name="get_question",
    title="Get question",
    access="read",
    description="Question text and its top answers with author and upvotes.",
    details=(
        "Returns one question with its text, answer count, followers and topics, and the top answers in the order "
        "Quora shows them, each with its full text. Use it before answering, so your agent sees what is already "
        "said. answers_limit set to 0 returns the question only."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /questions/by-url",
    example_response={
        "question_id": "44880608",
        "question": "Why is gravel cycling growing in popularity?",
        "question_url": "https://www.quora.com/Why-is-gravel-cycling-growing-in-popularity",
        "answers": 6,
        "followers": 2,
        "topics": ["Cycling", "Bicycles"],
        "viewer_has_answered": False,
        "top_answers": [
            {
                "answer_id": "205248839",
                "author": "Dana Reyes",
                "author_url": "https://www.quora.com/profile/Dana-Reyes",
                "text": "Most of it is the roads...",
                "url": "https://www.quora.com/Why-is-gravel-cycling-growing-in-popularity/answer/Dana-Reyes",
                "upvotes": 41,
                "views": 1200,
                "comments": 2,
                "shares": 0,
                "created_at": "2025-04-02T10:15:00Z",
            }
        ],
    },
)
async def get_question(ctx: ToolContext, args: dict[str, Any]) -> Any:
    slug = question_slug(args["question_url"])
    count = bounded(args, "answers_limit", 5, 20)
    state = await session(ctx)
    data = await graphql(
        ctx, state, "QuestionPageLoadablePreviewQuery", {"questionSlugEncoded": slug, "redirectedQid": None}
    )
    question = data.get("question")
    if not isinstance(question, dict) or question.get("isDeleted") or not question.get("qid"):
        raise ToolError("Quora has no question at that URL.", ErrorCode.TARGET_ERROR)
    result: dict[str, Any] = {
        "question_id": str(question["qid"]),
        "question": plain_text(question.get("title")),
        "question_url": absolute(question.get("url")),
        "answers": question.get("decanonicalizedAnswerCount", question.get("answerCount")),
        "followers": question.get("followerCount"),
        "topics": [
            topic.get("name") for topic in question.get("topics") or [] if isinstance(topic, dict) and topic.get("name")
        ],
        "viewer_has_answered": bool(question.get("viewerHasAnswered")),
        "top_answers": [],
    }
    if count == 0:
        return result
    variables = {
        "count": count,
        "cursor": "-1",
        "forceScoreVersion": None,
        "initial_count": min(count, 2),
        "topAid": None,
        "id": question["id"],
    }
    answers = await graphql(ctx, state, "QuestionPagedListPaginationQuery", variables)
    edges = (((answers.get("node") or {}).get("answers") or {}).get("edges")) or []
    for edge in edges:
        answer = ((edge or {}).get("node") or {}).get("answer")
        if isinstance(answer, dict) and answer.get("aid") and not answer.get("isDeleted"):
            result["top_answers"].append(answer_row(answer, with_question=False))
    result["top_answers"] = result["top_answers"][:count]
    return result
