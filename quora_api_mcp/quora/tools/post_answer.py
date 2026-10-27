"""Post answer: the question by URL, then `AnswerEditorMutation_answerCreate_Mutation`."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, question_slug, rich_text

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question_url": {"type": "string", "description": "Question URL on quora.com."},
        "body_markdown": {
            "type": "string",
            "description": "Answer text. Plain: a blank line starts a paragraph, no formatting or images.",
        },
    },
    "required": ["question_url", "body_markdown"],
    "additionalProperties": False,
}


@tool(
    name="post_answer",
    title="Post answer",
    access="write",
    confirm=True,
    description="Publish an answer as you under a question.",
    details=(
        "Publishes an answer under your name below the question you name, public at once. Quora allows one answer "
        "per person per question, and its rules forbid spam and copied text. By default you confirm each call; "
        "you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /answers",
    example_response={
        "answer_id": "391847562",
        "status": "published",
        "url": "https://www.quora.com/Which-gravel-roads-stay-rideable-a-day-after-heavy-rain/answer/Jordan-Lee",
        "created_at": "2026-10-27T14:20:00Z",
    },
)
async def post_answer(ctx: ToolContext, args: dict[str, Any]) -> Any:
    slug = question_slug(args["question_url"])
    body = str(args["body_markdown"]).strip()
    if not body:
        raise ToolError("body_markdown must not be empty.", ErrorCode.INVALID_INPUT)
    state = await session(ctx)
    page = await graphql(
        ctx, state, "QuestionPageLoadablePreviewQuery", {"questionSlugEncoded": slug, "redirectedQid": None}
    )
    question = page.get("question")
    if not isinstance(question, dict) or not question.get("qid") or question.get("isDeleted"):
        raise ToolError("Quora has no question at that URL.", ErrorCode.TARGET_ERROR)
    if question.get("viewerHasAnswered"):
        raise ToolError("You have already answered this question.", ErrorCode.TARGET_ERROR)
    if question.get("viewerCantAnswer") or question.get("isLocked"):
        raise ToolError("Quora does not let this account answer this question.", ErrorCode.TARGET_ERROR)
    variables = {
        "qid": question["qid"],
        "content": rich_text(body),
        "tribeId": None,
        "businessUid": None,
        "businessCustomAction": {"objectiveType": 2, "cta": 0},
        "accessOption": None,
        "captcha": None,
    }
    data = await graphql(ctx, state, "AnswerEditorMutation_answerCreate_Mutation", variables, write=True)
    # The page aliases the field: `answerSubmit {success, errorType, status, msg, answer {id, aid, content,
    # question {viewerAnswerUrl}}, redirectUrl}` (Relay artifact, 27.10.2026).
    submit = data.get("answerSubmit") or data.get("answerCreate") or {}
    answer: dict[str, Any] = submit["answer"] if isinstance(submit.get("answer"), dict) else {}
    if not submit.get("success") or not answer.get("aid"):
        reason = submit.get("msg") or submit.get("errorType") or submit.get("status")
        message = f"Quora did not publish the answer: {reason}" if reason else "Quora did not publish the answer."
        raise ToolError(message, ErrorCode.TARGET_ERROR)
    url = (answer.get("question") or {}).get("viewerAnswerUrl") or submit.get("redirectUrl")
    return {
        "answer_id": str(answer["aid"]),
        "status": "published",
        "url": absolute(url),
        "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
