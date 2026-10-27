"""Get Space stats: `TribeStatsOverview_Query` for all time and the last week, `TribeStatsTopContentSectionQuery`
for the top items.

Each series is a JSON scalar; its point shape was not seen yet (the dev Space had no stats day), so a point is
read as a number, a `[time, count]` pair or an object with a count field.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from quora_api_mcp.core.helpers import json_field
from quora_api_mcp.core.tools import tool
from quora_api_mcp.quora.client import graphql, session
from quora_api_mcp.quora.content import absolute, bounded, plain_text, space_id

if TYPE_CHECKING:
    from quora_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "space_id": {"type": "string", "description": "Space ID from list_my_spaces."},
        "top_limit": {"type": "integer", "description": "Top content items, 0 to 20. Default: 5."},
    },
    "required": ["space_id"],
    "additionalProperties": False,
}

SERIES = {
    "views": "viewSeries",
    "new_followers": "followerSeries",
    "upvotes": "upvoteSeries",
    "comments": "commentSeries",
    "new_items": "itemSeries",
}


def _point(point: Any) -> int:
    if isinstance(point, bool):
        return 0
    if isinstance(point, int | float):
        return int(point)
    if isinstance(point, list | tuple) and point:
        return _point(point[-1])
    if isinstance(point, dict):
        for key in ("count", "value", "metricCount", "y"):
            if isinstance(point.get(key), int | float):
                return int(point[key])
    return 0


def _totals(tribe: dict[str, Any]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for name, field in SERIES.items():
        series = json_field(tribe.get(field))
        totals[name] = sum(_point(point) for point in series) if isinstance(series, list) else 0
    return totals


def _top_item(item: dict[str, Any]) -> dict[str, Any]:
    content = item.get("post") or item.get("answer") or item.get("question") or item.get("contentObject") or {}
    question = content.get("question") if isinstance(content.get("question"), dict) else None
    title = plain_text(content.get("title")) or (plain_text(question.get("title")) if question else "")
    text = plain_text(content.get("content"))
    return {
        "type": str(content.get("__typename") or "").lower() or None,
        "title": title or text[:120] or None,
        "url": absolute(content.get("permaUrl") or content.get("url")),
        "views": item.get("viewCount"),
        "upvotes": item.get("upvoteCount"),
        "comments": item.get("commentCount"),
    }


@tool(
    name="get_space_stats",
    title="Get Space stats",
    access="read",
    description="Views, followers, upvotes, comments and new items of a Space, all-time and last 7 days, top content.",
    details=(
        "Returns the statistics Quora shows on a Space's Stats page, as totals for all time and for the last 7 "
        "days, plus the top content by views. Quora updates them once a day, after 5 pm Pacific time, so a new "
        "Space shows zeros. Visible to Space admins and moderators."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /spaces/{space_id}/stats",
    example_response={
        "space_id": "7310452",
        "all_time": {"views": 18240, "new_followers": 312, "upvotes": 521, "comments": 64, "new_items": 40},
        "last_7_days": {"views": 412, "new_followers": 3, "upvotes": 9, "comments": 1, "new_items": 2},
        "top_content": [
            {
                "type": "post",
                "title": "Pulling a first shot on a new espresso machine",
                "url": "https://homeespressonotes.quora.com/Pulling-a-first-shot-on-a-new-espresso-machine",
                "views": 930,
                "upvotes": 21,
                "comments": 4,
            }
        ],
    },
)
async def get_space_stats(ctx: ToolContext, args: dict[str, Any]) -> Any:
    tribe_id = space_id(args)
    top = bounded(args, "top_limit", 5, 20)
    state = await session(ctx)
    result: dict[str, Any] = {"space_id": str(tribe_id)}
    for key, interval in (("all_time", "all_time"), ("last_7_days", "week")):
        data = await graphql(ctx, state, "TribeStatsOverview_Query", {"tribeId": tribe_id, "interval": interval})
        result[key] = _totals(data.get("tribe") or {})
    result["top_content"] = []
    if top:
        variables = {
            "tribeId": tribe_id,
            "interval": "all_time",
            "metric": "view",
            "contentFilter": "without_question",
            "limit": top,
        }
        data = await graphql(ctx, state, "TribeStatsTopContentSectionQuery", variables)
        items = (data.get("tribe") or {}).get("topTribeContentListWithLimit") or []
        result["top_content"] = [_top_item(item) for item in items if isinstance(item, dict)]
    return result
