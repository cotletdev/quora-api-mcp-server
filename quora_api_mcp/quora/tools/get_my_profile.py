"""Get my profile: `UserProfilePageTabs_userQuery` and `UserProfileCredentialQuery` for the viewer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, user_name

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

# The profile page sends its tab labels as variables; without them Quora answers "Server Error".
TAB_LABELS = {
    "Activity": "Activity",
    "Answers": "Answers",
    "Combined": "Profile",
    "Edits": "Edits",
    "Followers": "Followers",
    "Following": "Following",
    "KnowsAbout": "Knows About",
    "Posts": "Posts",
    "Published": "Published",
    "Questions": "Questions",
}


@tool(
    name="get_my_profile",
    title="Get my profile",
    access="read",
    description="Your Quora name, headline, followers and counts of answers, questions and posts.",
    details=(
        "Returns the profile of the signed-in Quora account: name, profile URL, headline (the default credential), "
        "followers and following, how many answers, questions and posts it has, how many Spaces and topics it "
        "follows, and the topics it knows about."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /profile",
    example_response={
        "user_id": "1784520931",
        "name": "Jordan Lee",
        "profile_url": "https://www.quora.com/profile/Jordan-Lee",
        "headline": "Software developer",
        "followers": 12,
        "following": 30,
        "answers": 4,
        "questions": 1,
        "posts": 2,
        "spaces_followed": 3,
        "topics_followed": 6,
        "knows_about": ["Cycling", "Hiking"],
    },
)
async def get_my_profile(ctx: ToolContext, args: dict[str, Any]) -> Any:
    del args
    state = await session(ctx)
    data = await graphql(ctx, state, "UserProfilePageTabs_userQuery", {"uid": state.viewer_uid, **TAB_LABELS})
    user = data.get("user") or {}
    credential = await graphql(ctx, state, "UserProfileCredentialQuery", {"uid": state.viewer_uid})
    headline = ((credential.get("user") or {}).get("profileCredential") or {}).get("experience")
    topics = []
    for edge in (user.get("profileTopicsConnection") or {}).get("edges") or []:
        node = (edge or {}).get("node") or {}
        topic = node["topic"] if isinstance(node.get("topic"), dict) else node
        if topic.get("name"):
            topics.append(topic["name"])
    return {
        "user_id": str(state.viewer_uid),
        "name": user_name(user) or state.name,
        "profile_url": absolute(user.get("profileUrl")),
        "headline": headline,
        "followers": user.get("followerCount"),
        "following": user.get("followingCount"),
        "answers": user.get("numPublicAnswers"),
        "questions": user.get("numProfileQuestions"),
        "posts": user.get("postsCount"),
        "spaces_followed": user.get("numFollowedTribes"),
        "topics_followed": user.get("numFollowedTopics"),
        "knows_about": topics,
    }
