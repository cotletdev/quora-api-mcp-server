"""Ask question: `askQuestionStepUtils_questionCreate_Mutation`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, plain_text

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "question": {"type": "string", "description": "Question text, ending with a question mark."},
        "skip_duplicate_check": {
            "type": "boolean",
            "description": "Ask even when Quora suggests similar questions. Default: false.",
        },
    },
    "required": ["question"],
    "additionalProperties": False,
}


def _question(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not value.get("qid"):
        return None
    return {
        "question_id": str(value["qid"]),
        "question": plain_text(value.get("title")) or None,
        "question_url": absolute(value.get("url")),
    }


@tool(
    name="ask_question",
    title="Ask question",
    access="write",
    confirm=True,
    description="Add a new public question to Quora.",
    details=(
        "Adds a new question under your name, public at once. When the same question already exists, Quora "
        "returns it instead (status exists). When Quora finds similar ones, nothing is asked and they come back "
        "as status similar_found: answer one of them, or call again with skip_duplicate_check. By default you "
        "confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /questions",
    example_response={
        "status": "published",
        "question_id": "180234411",
        "question": "Which gravel roads stay rideable a day after heavy rain?",
        "question_url": "https://www.quora.com/Which-gravel-roads-stay-rideable-a-day-after-heavy-rain",
        "similar": [],
    },
)
async def ask_question(ctx: ToolContext, args: dict[str, Any]) -> Any:
    text = " ".join(str(args["question"]).split())
    if len(text) < 10:
        raise ToolError("question must be a full question.", ErrorCode.INVALID_INPUT)
    if not text.endswith("?"):
        text = f"{text}?"
    check = not bool(args.get("skip_duplicate_check"))
    state = await session(ctx)
    variables = {
        "titlePlaintext": text,
        "sourceLocation": 1,
        "limitedUserDistro": False,
        "targetType": None,
        "targetOid": None,
        "shouldCheckDuplicate": check,
        "shouldCheckCorrection": check,
        "shouldQueue": None,
    }
    data = await graphql(ctx, state, "askQuestionStepUtils_questionCreate_Mutation", variables, write=True)
    created = data.get("questionCreate") or {}
    similar = [row for row in (_question(item) for item in created.get("duplicateSuggestions") or []) if row]
    for status, field in (("published", "question"), ("exists", "existingQuestion"), ("exists", "redirectToQuestion")):
        row = _question(created.get(field))
        if row:
            return {"status": status, **row, "similar": similar}
    if similar:
        return {
            "status": "similar_found",
            "question_id": None,
            "question": text,
            "question_url": None,
            "similar": similar,
        }
    raise ToolError("Quora did not add the question.", ErrorCode.TARGET_ERROR)
