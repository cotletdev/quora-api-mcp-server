"""Quora's data shapes turned into tool output and back.

Rich text is a JSON string of sections, one per paragraph; node ids are base64 of `{Type}@0:{number}`;
times are microseconds since the epoch; URLs are often paths on www.quora.com.
"""

from __future__ import annotations

import base64
import json
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import unquote, urlparse

from quora_api_mcp.core.errors import ErrorCode, ToolError
from quora_api_mcp.quora.client import WEB


def plain_text(document: Any) -> str:
    """The text of a rich text JSON string (or its parsed dict), paragraphs joined by blank lines."""
    if isinstance(document, str):
        try:
            document = json.loads(document)
        except ValueError:
            return document
    if not isinstance(document, dict):
        return ""
    paragraphs = []
    for section in document.get("sections") or []:
        text = "".join(str(span.get("text") or "") for span in section.get("spans") or [])
        paragraphs.append(text)
    return "\n\n".join(part for part in paragraphs if part.strip()).strip()


def rich_text(text: str) -> str:
    """Plain text as Quora's rich text: one plain section per paragraph (blank line or line break)."""
    paragraphs = [line.strip() for line in re.split(r"\n+", text) if line.strip()] or [""]
    sections = [
        {
            "type": "plain",
            "indent": 0,
            "quoted": False,
            "is_rtl": False,
            "spans": [{"modifiers": {}, "text": paragraph}],
        }
        for paragraph in paragraphs
    ]
    return json.dumps({"sections": sections}, separators=(",", ":"))


def bounded(args: dict[str, Any], key: str, default: int, maximum: int) -> int:
    """An optional count from the input where 0 is allowed, clamped to 0..maximum."""
    value = args.get(key)
    return max(0, min(int(value) if isinstance(value, int | float | str) and str(value).strip() else default, maximum))


def node_id(kind: str, number: int) -> str:
    return base64.b64encode(f"{kind}@0:{number}".encode()).decode()


def iso(microseconds: Any) -> str | None:
    if not isinstance(microseconds, int) or microseconds <= 0:
        return None
    return datetime.fromtimestamp(microseconds / 1_000_000, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def absolute(url: Any) -> str | None:
    if not isinstance(url, str) or not url:
        return None
    return url if url.startswith("http") else f"{WEB}{url}"


def user_name(user: Any) -> str | None:
    if not isinstance(user, dict):
        return None
    if user.get("isAnon"):
        return "Anonymous"
    for name in user.get("names") or []:
        full = " ".join(part for part in (name.get("givenName"), name.get("familyName")) if part)
        if full:
            return full
    return None


def question_slug(question_url: str) -> str:
    """The slug of a question URL (`https://www.quora.com/Why-is-...`), as the question page query takes it."""
    raw = str(question_url).strip()
    parsed = urlparse(raw if "://" in raw else f"{WEB}/{raw.lstrip('/')}")
    host = parsed.netloc.lower()
    if host and not host.endswith("quora.com"):
        raise ToolError("question_url must be a question URL on quora.com.", ErrorCode.INVALID_INPUT)
    segments = [part for part in unquote(parsed.path).split("/") if part]
    if segments and segments[0] == "unanswered":
        segments = segments[1:]
    slug = segments[0] if segments else ""
    if not slug or slug in {"profile", "topic", "q", "search", "answer", "spaces"}:
        raise ToolError("question_url must be a question URL on quora.com.", ErrorCode.INVALID_INPUT)
    return slug


def space_id(args: dict[str, Any]) -> int:
    value = str(args.get("space_id") or "").strip()
    if not value.isdigit():
        raise ToolError("space_id must be the number from list_my_spaces.", ErrorCode.INVALID_INPUT)
    return int(value)


def answer_row(answer: dict[str, Any], *, with_question: bool) -> dict[str, Any]:
    row: dict[str, Any] = {
        "answer_id": str(answer.get("aid")),
        "author": user_name(answer.get("author")),
        "author_url": absolute((answer.get("author") or {}).get("profileUrl")),
        "text": plain_text(answer.get("content")),
        "url": absolute(answer.get("permaUrl") or answer.get("url")),
        "upvotes": answer.get("numUpvotes"),
        "views": answer.get("numViews"),
        "comments": answer.get("numDisplayComments"),
        "shares": answer.get("numShares"),
        "created_at": iso(answer.get("creationTime")),
    }
    question = answer.get("question")
    if with_question and isinstance(question, dict):
        row["question"] = plain_text(question.get("title"))
        row["question_url"] = absolute(question.get("url"))
    return row


def question_row(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": str(question.get("qid")),
        "question": plain_text(question.get("title")),
        "question_url": absolute(question.get("url")),
        "answers": question.get("decanonicalizedAnswerCount", question.get("answerCount")),
        "followers": question.get("followerCount"),
        "locked": bool(question.get("isLocked")),
    }


def find_all(value: Any, key: str) -> list[dict[str, Any]]:
    """Every dict under `value` that has `key`, depth first: for multifeed stories whose nesting varies."""
    found: list[dict[str, Any]] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if key in item:
                found.append(item)
            stack.extend(reversed(list(item.values())))
        elif isinstance(item, list):
            stack.extend(reversed(item))
    return found
