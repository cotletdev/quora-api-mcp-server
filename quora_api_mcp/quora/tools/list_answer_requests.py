"""List answer requests: `HighPriA2aRequestsListQuery` and `LowPriA2aRequestsListQuery`.

The edge shape was not seen yet (nobody has asked our test account), so the question and the sender are found
by their fields (`qid`, `names`) anywhere in the edge node.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.helpers import limit
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, find_all, iso, plain_text, user_name

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"limit": {"type": "integer", "description": "1 to 50. Default: 20."}},
    "required": [],
    "additionalProperties": False,
}

LISTS = (
    ("top", "HighPriA2aRequestsListQuery", "highPriA2asConnection"),
    ("other", "LowPriA2aRequestsListQuery", "lowPriA2asConnection"),
)


def _row(node: dict[str, Any], priority: str) -> dict[str, Any] | None:
    questions = [item for item in find_all(node, "qid") if item.get("title")]
    if not questions:
        return None
    question = questions[0]
    senders = [item for item in find_all(node, "names") if item.get("uid") != (question.get("asker") or {}).get("uid")]
    sent = next((item.get("sendTime") for item in find_all(node, "sendTime")), None)
    return {
        "question": plain_text(question.get("title")),
        "question_url": absolute(question.get("url")),
        "answers": question.get("decanonicalizedAnswerCount", question.get("answerCount")),
        "requested_by": user_name(senders[0]) if senders else None,
        "requested_at": iso(sent),
        "priority": priority,
    }


@tool(
    name="list_answer_requests",
    title="List answer requests",
    access="read",
    description="Questions other people asked you to answer.",
    details=(
        "Lists the requests on your Answer Requests page, Top requests first, then Other requests, with the "
        "question and who asked. Anyone on Quora can send a request to anyone, so expect questions outside your "
        "topics. Pass question_url to get_question."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /answer-requests",
    example_response={
        "requests": [
            {
                "question": "What is a good first gravel loop for a beginner?",
                "question_url": "https://www.quora.com/What-is-a-good-first-gravel-loop-for-a-beginner",
                "answers": 2,
                "requested_by": "Sam Ortiz",
                "requested_at": "2026-10-09T08:12:00Z",
                "priority": "top",
            }
        ]
    },
)
async def list_answer_requests(ctx: ToolContext, args: dict[str, Any]) -> Any:
    count = limit(args, 20, 50)
    state = await session(ctx)
    requests: list[dict[str, Any]] = []
    for priority, operation, field in LISTS:
        if len(requests) >= count:
            break
        variables = {"first": count - len(requests), "after": None, "sortSendTimeAsc": None}
        data = await graphql(ctx, state, operation, variables)
        connection = (data.get("viewer") or {}).get(field) or {}
        for edge in connection.get("edges") or []:
            row = _row(edge.get("node") or edge, priority) if isinstance(edge, dict) else None
            if row is not None:
                requests.append(row)
    return {"requests": requests[:count]}
