"""List my Spaces: `YourSpacesSortedByRole_Paging_Query`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

# viewerPermission: 3 seen on the Space our test account made (owner and admin). 1 and 2 follow the order of
# Quora's roles and are not confirmed yet.
ROLES = {0: "follower", 1: "contributor", 2: "moderator", 3: "admin"}
PAGE = 50
MAX_PAGES = 10


@tool(
    name="list_my_spaces",
    title="List my Spaces",
    access="read",
    description="Spaces you follow or help run, with your role.",
    details=(
        "Lists your Spaces with your role in each: admin, moderator, contributor or follower, the ones you run "
        "first. The role decides what you can do: admins, moderators and contributors can post, and only admins "
        "and moderators see stats and submissions. Use space_id in the other Space tools."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /spaces",
    example_response={
        "spaces": [
            {
                "space_id": "7310452",
                "name": "Home Espresso Notes",
                "role": "admin",
                "url": "https://homeespressonotes.quora.com",
            }
        ]
    },
)
async def list_my_spaces(ctx: ToolContext, args: dict[str, Any]) -> Any:
    del args
    state = await session(ctx)
    spaces: list[dict[str, Any]] = []
    after: str | None = None
    for _ in range(MAX_PAGES):
        data = await graphql(ctx, state, "YourSpacesSortedByRole_Paging_Query", {"first": PAGE, "after": after})
        connection = ((data.get("viewer") or {}).get("user") or {}).get("tribesSortedByRoleConnection") or {}
        for edge in connection.get("edges") or []:
            tribe = (edge or {}).get("node") or {}
            if not tribe.get("tribeId"):
                continue
            permission = tribe.get("viewerPermission") or 0
            spaces.append(
                {
                    "space_id": str(tribe["tribeId"]),
                    "name": tribe.get("nameString"),
                    "role": ROLES.get(permission, "follower"),
                    "url": tribe.get("url"),
                }
            )
        page = connection.get("pageInfo") or {}
        if not page.get("hasNextPage") or not page.get("endCursor"):
            break
        after = page["endCursor"]
    return {"spaces": spaces}
