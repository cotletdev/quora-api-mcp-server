"""Review Space submission: accept, add to queue or reject (pass) mutations by `submissionId`.

Not run on a real submission yet: the dev Space has none."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import space_id

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "space_id": {"type": "string", "description": "Space ID from list_my_spaces."},
        "submission_id": {"type": "string", "description": "Submission ID from list_space_submissions."},
        "action": {"type": "string", "enum": ["approve", "queue", "pass"], "description": "approve, queue or pass."},
    },
    "required": ["space_id", "submission_id", "action"],
    "additionalProperties": False,
}

ACTIONS = {
    "approve": ("SubmissionAcceptButton_tribeSubmissionAccept_Mutation", "tribeSubmissionAccept", "approved"),
    "queue": (
        "SubmissionQueueButton_tribeSubmissionAddToContentQueue_Mutation",
        "tribeSubmissionAddToContentQueue",
        "queued",
    ),
    "pass": ("SubmissionRejectButton_tribeSubmissionReject_Mutation", "tribeSubmissionReject", "passed"),
}


@tool(
    name="review_space_submission",
    title="Review Space submission",
    access="write",
    confirm=True,
    description="Approve, queue or pass on a follower submission. Space admins and moderators only.",
    details=(
        "Approve publishes the submission in the Space at once. Queue adds it to the Space queue. Pass removes it "
        "from the pending list. By default you confirm each call; you can switch that off for this tool."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /spaces/{space_id}/submissions/{submission_id}/review",
    example_response={"submission_id": "88412", "space_id": "7310452", "status": "approved"},
)
async def review_space_submission(ctx: ToolContext, args: dict[str, Any]) -> Any:
    tribe_id = space_id(args)
    submission = str(args["submission_id"]).strip()
    if not submission.isdigit():
        raise ToolError("submission_id must be the number from list_space_submissions.", ErrorCode.INVALID_INPUT)
    action = str(args["action"])
    if action not in ACTIONS:
        raise ToolError("action must be approve, queue or pass.", ErrorCode.INVALID_INPUT)
    operation, field, status = ACTIONS[action]
    state = await session(ctx)
    data = await graphql(ctx, state, operation, {"submissionId": int(submission)}, write=True)
    if not data.get(field):
        raise ToolError("Quora did not take the review. Check the submission ID.", ErrorCode.TARGET_ERROR)
    return {"submission_id": submission, "space_id": str(tribe_id), "status": status}
