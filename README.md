# Quora API and MCP server, self-hosted

<!-- mcp-name: dev.cotlet/quora -->

A **Quora API** and a **Quora MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. All 13 Quora tools we run in production at [Cotlet](https://cotlet.dev/integrations/quora-api-mcp-server): search questions, read answers, post answers, ask questions, answer requests, notifications, and Spaces with their stats, posts and submissions.

Quora has no public API and no official MCP server. This repo gives you both:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/quora`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("search_questions", query="espresso grinder")`, plus 11 ready scripts in [`examples/`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/).

It is for technical people who want to run it themselves, **for noncommercial use only** ([license](#license)). If you want it running 24/7 on a server, kept working when Quora changes its site, for a team or a business, use the [hosted version at cotlet.dev](https://cotlet.dev/integrations/quora-api-mcp-server).

[![Quora MCP server](https://img.shields.io/badge/Quora%20MCP-13%20tools-b92b27)](#all-13-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-141318)](https://github.com/cotletdev/quora-api-mcp-server/blob/main/LICENSE)

```bash
uv tool install quora-api-mcp                  # or: pip install quora-api-mcp
quora-mcp connect                              # reads your Quora session from Chrome
quora-mcp call search_questions query=espresso limit=5
claude mcp add quora -- uvx quora-api-mcp mcp
```

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 13 tools](#all-13-tools)
- [Configuration](#configuration)
- [Security and your Quora account](#security-and-your-quora-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ quora-mcp on your computer ──your Quora cookies──▶ www.quora.com
                                                  ▲
                         quora-mcp connect ───────┘ reads them once from your Chrome (DevTools Protocol)
```

1. You sign in to Quora in your own Chrome, the way you always do.
2. `quora-mcp connect` attaches to that Chrome through the Chrome DevTools Protocol, reads the quora.com cookies and saves them to `~/.config/quora-api-mcp/session.json`, readable by your user only. It never sees or stores your password.
3. Every tool call first reads Quora's front page for the headers its web app sends (form key, revision), then calls the GraphQL endpoints the web app calls, with your cookies. Requests go out with [curl_cffi](https://github.com/lexiforest/curl_cffi), which copies Chrome's TLS fingerprint. No headless browser runs.

Cloudflare guards www.quora.com. Without its `cf_clearance` cookie every request gets a 403. `connect` reads that cookie along with your session, and Cloudflare ties it to your Chrome and your network. So run the server on the same computer and internet connection as the Chrome you connected. Even then Cloudflare answers the odd request with a bot check: the tool fails with `target_blocked`, and a retry usually passes. If it keeps failing, open quora.com in that Chrome, pass the check if one shows, and run `quora-mcp connect` again.

When Quora signs you out, the server reads the cookies from Chrome again, if Chrome is open with remote debugging on.

## Requirements

- Python 3.11 or newer.
- Google Chrome 144 or newer, signed in to Quora. Any Chrome or Chromium works with a [debugging port](#option-b-a-chrome-with-a-debugging-port).
- macOS, Linux or Windows, on the same network as that Chrome ([why](#how-it-works)).
- The Space role a tool needs: Space stats and submissions need admin or moderator, posting needs admin, moderator or contributor. Search, questions, your answers and notifications work with any Quora account.

## Install

From [PyPI](https://pypi.org/project/quora-api-mcp/):

```bash
uv tool install quora-api-mcp       # or: pipx install quora-api-mcp, or: pip install quora-api-mcp
quora-mcp --version
```

MCP clients can also run it with no install: `uvx quora-api-mcp mcp`.

From source:

```bash
git clone https://github.com/cotletdev/quora-api-mcp-server.git
cd quora-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
quora-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run quora-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `uv tool upgrade quora-api-mcp` (or `pip install -U quora-api-mcp`), from source `git pull && pip install -e .`. We copy every change of the hosted Quora tools into this repo.

## Connect your Chrome

### Option A: your everyday Chrome (recommended)

1. Open `chrome://inspect/#remote-debugging` in Chrome and switch **remote debugging** on. Chrome then accepts DevTools connections from programs on this computer, and asks you before each one.
2. Open [quora.com](https://www.quora.com) and make sure you are signed in. That visit also gives this Chrome its Cloudflare cookie.
3. Run:

   ```bash
   quora-mcp connect
   ```

4. Chrome asks whether to allow the connection. Click **Allow**.

```text
Saved 31 Quora cookies to /Users/you/.config/quora-api-mcp/session.json
Signed in to Quora as Ana Lopez
```

You can switch remote debugging off again afterwards. Leave it on if you want the server to pick up a new session by itself after Quora signs you out.

`connect` looks for Chrome's `DevToolsActivePort` file in the default profile folder. For Chrome Beta, Canary or a custom profile folder, pass `--profile-dir "<folder>"`.

### Option B: a Chrome with a debugging port

Chrome does not open a debugging port on your default profile, so start a separate one, sign in to Quora there once, and connect to it:

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-quora"
# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-quora"
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-quora"

quora-mcp connect --cdp http://127.0.0.1:9222
```

`--cdp` also takes a `ws://` DevTools URL, for example of a Chrome on another machine reached over an SSH tunnel. Requests still leave from the machine that runs `quora-mcp`, so Cloudflare may answer them with a bot check.

### Option C: paste the cookie by hand

In Chrome open DevTools on quora.com, **Application > Cookies > https://www.quora.com**, copy the value of `m-b`, then:

```bash
quora-mcp connect --token          # paste it, input is hidden
# or, without a session file:
export QUORA_AUTH_TOKEN=...
```

A pasted cookie is not refreshed on its own, and it carries no Cloudflare cookie, so Quora will most likely answer with a 403. Options A and B work better.

Check the session at any time:

```bash
quora-mcp status
```

## MCP server

The MCP server lists every tool with its input schema, a description written for agents, and hints: read tools are marked read-only, and tools that publish are marked so your client asks before running them.

### Claude Code

```bash
claude mcp add quora -- uvx quora-api-mcp mcp
# read only:
claude mcp add quora -- uvx quora-api-mcp mcp --read-only
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "quora": {
      "command": "uvx",
      "args": ["quora-api-mcp", "mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.quora]
command = "uvx"
args = ["quora-api-mcp", "mcp"]
```

### Over HTTP

`quora-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
quora-mcp serve
claude mcp add --transport http quora http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *Find questions about home espresso with fewer than five answers and draft an answer for the best three.*
>
> *What did people ask me to answer this week? Sort them by how many answers they already have.*
>
> *Show the pending submissions in my Space and approve the ones on topic.*
>
> *Compare views and new followers of my Spaces for the last 7 days.*

## REST API

```bash
quora-mcp serve                    # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/quora`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments, and a JSON body adds the rest.

```bash
curl 'http://127.0.0.1:8787/api/v1/quora/questions/search?query=espresso&limit=5'
curl 'http://127.0.0.1:8787/api/v1/quora/questions/by-url?question_url=https://www.quora.com/How-do-I-make-a-great-cup-of-espresso'
curl 'http://127.0.0.1:8787/api/v1/quora/spaces/1234567/stats'
curl -X POST http://127.0.0.1:8787/api/v1/quora/spaces/1234567/posts \
  -H 'Content-Type: application/json' \
  -d '{"title": "Dialing in a light roast", "body_markdown": "Start two steps finer than for a medium roast.", "mode": "queue"}'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/quora/tools/search_questions -d '{"query": "espresso"}'
```

- `GET /api/v1/quora/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.
- Answers are JSON. Lists return `next_cursor`; pass it back as `cursor` for the next page.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
QUORA_MCP_TOKEN=$(openssl rand -hex 24) quora-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from quora_api_mcp import call
from quora_api_mcp.scripting import paginate, write_rows

questions = list(paginate("search_questions", {"query": "espresso grinder"}, "questions", max_items=100))
write_rows([q for q in questions if q["answers"] < 5], "questions.csv")
spaces = call("list_my_spaces")["spaces"]
```

Or one tool from the shell: `quora-mcp call list_my_answers limit=10`, or with a JSON object.

Ready scripts in [`examples/`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/). Each prints JSON, takes `--out file.csv` or `--out file.json` where it makes sense, and `--help`:

| Script | What it does |
|---|---|
| [`find_questions.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/find_questions.py) | Questions on a topic worth answering: few answers, not locked. `--max-answers`, `--out`. |
| [`answer_requests.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/answer_requests.py) | Questions other people asked you to answer, with who asked. |
| [`read_question.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/read_question.py) | One question with its top answers, and whether you have answered it. |
| [`post_answer.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/post_answer.py) | Publishes an answer from `--body` or a file, after checking you have not answered yet. `--dry-run` first. |
| [`ask_question.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/ask_question.py) | Asks a question, unless Quora finds similar ones. `--anyway` asks regardless. |
| [`export_my_answers.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/export_my_answers.py) | Your answers to CSV or JSON: question, text, URL, views, upvotes, date. |
| [`my_spaces.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/my_spaces.py) | Spaces you follow or help run, with your role and Space ID. `--role admin`. |
| [`post_to_space.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/post_to_space.py) | Posts in a Space now, or adds the post to its queue with `--queue`. |
| [`review_submissions.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/review_submissions.py) | Lists follower submissions to your Space, then approves, queues or passes them. `--dry-run`. |
| [`space_stats.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/space_stats.py) | Views, new followers, upvotes and comments of every Space you run, 7 days and all time. |
| [`notifications.py`](https://github.com/cotletdev/quora-api-mcp-server/blob/main/examples/notifications.py) | Your profile counts and unread notifications. |

```bash
python examples/find_questions.py --query "home espresso" --max-answers 3 --out questions.csv
python examples/review_submissions.py --space 1234567 --approve-all --dry-run
```

On a schedule, cron on your own computer works while it is on: `0 8 * * 1 cd ~/quora-api-mcp-server && .venv/bin/python examples/space_stats.py --out stats.csv`.

## All 13 tools

Space IDs come from `list_my_spaces`, question URLs from `search_questions`. `quora-mcp tools` prints this list, `quora-mcp tools --json` adds the input schemas.

### Questions and answers

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `search_questions` | read | `GET /questions/search` | Questions matching a keyword, with answer counts. |
| `get_question` | read | `GET /questions/by-url` | Question text and its top answers with author and upvotes. |
| `post_answer` | write | `POST /answers` | Publish an answer as you under a question. |
| `ask_question` | write | `POST /questions` | Add a new public question to Quora. |

### Your account

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_my_profile` | read | `GET /profile` | Your Quora name, headline, followers and counts of answers, questions and posts. |
| `list_my_answers` | read | `GET /answers` | Your answers with question, text, URL and views, newest first. |
| `list_answer_requests` | read | `GET /answer-requests` | Questions other people asked you to answer. |
| `list_notifications` | read | `GET /notifications` | Your Quora notifications, newest first: answers, upvotes, follows, Space invites. |

### Spaces

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_my_spaces` | read | `GET /spaces` | Spaces you follow or help run, with your role. |
| `get_space_stats` | read | `GET /spaces/{space_id}/stats` | Views, followers, upvotes, comments and new items of a Space, all-time and last 7 days, top content. |
| `list_space_submissions` | read | `GET /spaces/{space_id}/submissions` | Answers, posts and questions followers submitted to your Space, waiting for review. |
| `post_to_space` | write | `POST /spaces/{space_id}/posts` | New post in a Space you contribute to, posted now or added to its queue. |
| `review_space_submission` | write | `POST /spaces/{space_id}/submissions/{submission_id}/review` | Approve, queue or pass on a follower submission. Space admins and moderators only. |

Text you publish goes out as plain paragraphs: a blank line starts a new one, no formatting, links or images. No tool edits or deletes an answer, question or post yet. Never built, on purpose: your Quora sign-in, email, password and account settings, and anything that moves money. Every request passes a guard that refuses sign-in, password and email paths.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `QUORA_MCP_HOME` | `~/.config/quora-api-mcp` | Folder of `session.json`. |
| `QUORA_AUTH_TOKEN` | | Quora `m-b` cookie, instead of `quora-mcp connect`. |
| `QUORA_PROXY` | | Proxy for every request to Quora, e.g. `http://user:pass@host:port`. Cloudflare's cookie works only from the network Chrome used. |
| `QUORA_MCP_READ_ONLY` | | `1` hides and refuses every tool that changes Quora (same as `--read-only`). |
| `QUORA_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `QUORA_MCP_HOST`, `QUORA_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |

## Security and your Quora account

- **Your password never reaches this code.** Only cookies are read, and only those of quora.com.
- **The session file is yours.** `session.json` is created with mode 0600. Anyone who has it can act as you on Quora, so keep it out of git and shared folders.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `QUORA_MCP_TOKEN`.
- **quora.com only.** Requests and redirects outside quora.com are refused.
- **Read-only mode.** `--read-only` or `QUORA_MCP_READ_ONLY=1` exposes the 9 read tools only.
- **Writes are public.** Answers, questions and Space posts go out under your name, and an approval publishes someone else's submission. MCP clients ask before running them; a script does not.
- **Keep to normal use.** Quora bans fast posters and answer bots. Post a few answers a day at most, never the same text twice, and search no more than you would by hand. You are responsible for what runs in your account.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required`, `auth_expired` | No session, or Quora signed you out. Sign in to Quora in Chrome and run `quora-mcp connect`. |
| 403 | `target_blocked` | Cloudflare answered with a bot check. Retry once. If it repeats, open quora.com in the Chrome you connected, then run `quora-mcp connect` again on the same network. |
| 403 | `scope_denied` | The server runs read-only. |
| 422 | `invalid_input` | An argument is missing or wrong; the message names it. |
| 429 | `rate_limited` | Quora is limiting the account. Wait a few minutes. |
| 502 | `target_error` | Quora refused the request (a wrong ID or URL, a Space role too low), or changed its site. Check the arguments, `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/quora-api-mcp-server/issues). |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/quora-api-mcp-server) |
|---|---|---|
| Tools | the same 13 | the same 13 |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| Quora session | your Chrome, cookies in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM |
| Cloudflare bot checks | your Chrome and your network | passed in your Cloud Browser |
| When Quora changes its site | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Approvals | your MCP client asks per call | answers, questions, Space posts and reviews wait for your OK, switchable per tool |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, any HTTP client |
| Who may use it | you, for noncommercial use | teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 10 credits, failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Does Quora have an official API?**
No. Quora has no public API and no developer docs. Its help center covers only the web and mobile apps. Details: [cotlet.dev/integrations/quora-api-mcp-server](https://cotlet.dev/integrations/quora-api-mcp-server).

**Is there a Quora MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `quora-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted Quora MCP server](https://cotlet.dev/integrations/quora-api-mcp-server) gives you.

**Is this a Quora scraper?**
It reads what people want a scraper for (questions, answers, your own stats) but parses no HTML in a headless browser. It calls the GraphQL endpoints the Quora web app calls, in your own account, and it can also write: answers, questions, Space posts and submission reviews.

**Why do I get a 403 or `target_blocked`?**
Cloudflare. Its `cf_clearance` cookie works only from the network and browser that got it. Run `quora-mcp` on the computer whose Chrome you connected, open quora.com in that Chrome once, and run `quora-mcp connect` again. Turning a VPN on or off in between breaks it too.

**Can it run on a VPS or in Docker?**
Rarely. Cloudflare blocks most datacenter IPs, and the cookie from your home Chrome does not work from a server. A Chrome on the server reached with `--cdp` gets its own Cloudflare cookie, but Quora may still show it a check that a person has to pass. For an always-on setup the hosted version keeps your session in your own Cloud Browser.

**Can I export my Quora answers?**
Yes: `python examples/export_my_answers.py --out answers.csv`. Every answer with its question, text, URL, views and upvotes.

**Which Space role do I need?**
Posting needs admin, moderator or contributor. Stats and submissions need admin or moderator. As a follower, `post_to_space` sends the post to the Space admins for review (status `submitted`). `list_my_spaces` shows your role in each Space.

**Why does my Space show zero views?**
Quora updates Space statistics once a day, after 5 pm Pacific time. A Space made today shows zeros until then.

**Will my Quora account get banned?**
Quora bans fast posters and answer bots. Requests carry Chrome's fingerprint and go out one at a time, but nobody can promise a platform never acts. Keep the volume to what you would write by hand.

**Can I use it at work or for my clients?**
No, the license allows noncommercial use only. For a team, a company or client work, use [Cotlet](https://cotlet.dev) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Is it open source?**
The source is public, the license is not an open source license: noncommercial use only, no business use.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/quora-api-mcp-server/issues) with the tool name and the error message.

## License

[PolyForm Noncommercial License 1.0.0](https://github.com/cotletdev/quora-api-mcp-server/blob/main/LICENSE). In short:

- **Allowed:** noncommercial use: you, for your own personal purposes with your own Quora account, or a charity, school, public research or government body. Changing the code, and sharing it under the same license.
- **Not allowed:** any commercial use, your own business included; client work; selling or offering it, or a service built on it.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/cotletdev/quora-api-mcp-server/main/assets/logo-white.svg">
      <img src="https://raw.githubusercontent.com/cotletdev/quora-api-mcp-server/main/assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev) ([@cotletdev](https://x.com/cotletdev)). Quora is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by Quora.
