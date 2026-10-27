# AGENTS.md

You are an AI agent in a clone of this repo. It is a self-hosted Quora API and MCP server: 13 tools that work in the user's own Quora account, through the session of their own Google Chrome. Your usual job is one of three: set it up for the user, use its tools for them, or change its code. Human docs: `README.md`.

## Before you start

- The license allows noncommercial use only (PolyForm Noncommercial 1.0.0, `LICENSE`). If the user is setting this up for a company, a team or clients, say so and point to the hosted version at https://cotlet.dev/integrations/quora-api-mcp-server. Do not continue the setup for that use.
- Every tool acts as the user on Quora. Tools with access `write` publish answers, questions and Space posts, or approve submissions, and real people see the result.

## Set it up for the user

Do the steps yourself. Ask the user only for what needs their hands in Chrome.

1. Check Python: `python3 --version` must be 3.11 or newer.
2. Install in the repo root:

   ```bash
   python3 -m venv .venv && .venv/bin/pip install -e .
   .venv/bin/quora-mcp --version
   ```

   On Windows the path is `.venv\Scripts\quora-mcp`. With uv: `uv venv && uv pip install -e .`.
3. Ask the user to do two things in Chrome. You cannot open `chrome://` pages for them.
   - Open `chrome://inspect/#remote-debugging` and switch remote debugging on.
   - Open https://www.quora.com and be signed in there.
4. Run `.venv/bin/quora-mcp connect`. Tell the user to click **Allow** when Chrome asks about the connection. Success prints `Signed in to Quora as <name>`.
5. Check: `.venv/bin/quora-mcp status`, then `.venv/bin/quora-mcp call get_my_profile`.
6. Add the MCP server to the user's client. Use the absolute path of `.venv/bin/quora-mcp`:
   - Claude Code: `claude mcp add quora -- <abs path>/.venv/bin/quora-mcp mcp`
   - Claude Desktop, Cursor, Codex: the config blocks in `README.md`, section "MCP server".
   - Add `--read-only` after `mcp` if the user only wants to read.
   The client loads new MCP servers on its next start. Tell the user.

Run the server on the same computer as the Chrome you connected. Cloudflare guards www.quora.com, and its cookie works only from the network that Chrome uses.

If step 4 or 5 fails:

| Message | What to do |
|---|---|
| `Chrome remote debugging is off` | Step 3 is not done, or Chrome is Beta, Canary or a custom profile: pass `--profile-dir "<profile folder>"`. |
| `Could not connect to Chrome` | The user did not click Allow, or Chrome is closed. Run `connect` again. |
| `This Chrome is not signed in to Quora` | The user signs in at quora.com in that Chrome, then run `connect` again. |
| `target_blocked: Quora showed a bot check` | Run the same command once more. If it repeats, the user opens quora.com in the same Chrome and passes the check if one shows. Then run `connect` again. |
| No Chrome on this machine (a server) | Quora's Cloudflare blocks most servers. Point the user to the hosted version. A pasted cookie (`quora-mcp connect --token`, cookie `m-b`) is for the user to run themselves; never ask them to paste it into the chat. |

## Use the tools

- With the MCP server added, call its tools. Without it: `.venv/bin/quora-mcp call <tool> key=value ...`, or one JSON object as the argument.
- `.venv/bin/quora-mcp tools` lists every tool with access and route. `tools --json` adds the input schemas.
- Start with `get_my_profile`. Questions come from `search_questions` and `list_answer_requests`; their `question_url` goes to `get_question` and `post_answer`. Space tools take the `space_id` from `list_my_spaces`.
- Lists return `next_cursor`. Pass it back as `cursor` for the next page.
- Before a `write` tool, show the user the exact text and where it goes, and get their OK. Quora bans fast posters and answer bots: never post answers or Space posts in a loop, and never the same text twice.
- For a script or a cron job, use `quora_api_mcp.scripting` (`call`, `paginate`, `write_rows`) and the scripts in `examples/` as models.
- For a REST API (n8n, other languages): `.venv/bin/quora-mcp serve`, routes under `http://127.0.0.1:8787/api/v1/quora`, docs at `/docs`.

Errors come as `<code>: <message>`. `auth_expired` means Quora signed the session out: the user signs in again in Chrome and you run `connect`. `target_blocked` is a Cloudflare bot check: see the table above. `target_error` usually means a wrong ID or URL, or a Space role too low for the tool. More codes: `README.md`, section "Errors".

## Keep secrets out

- `~/.config/quora-api-mcp/session.json` and `QUORA_AUTH_TOKEN` give full access to the user's Quora account. Never print, log, commit or copy their content.
- `serve` listens on 127.0.0.1. Never start it on another address without `QUORA_MCP_TOKEN`.

## Change the code

| Path | What | Edit? |
|---|---|---|
| `quora_api_mcp/quora/` | the Quora tools, one file per tool in `tools/`, the front page and GraphQL calls in `client.py`, operation hashes in `operations.py` | Yes for a local fix, but the next `git pull` brings our version of these files. Report the bug at https://github.com/cotletdev/quora-api-mcp-server/issues |
| `quora_api_mcp/app.py` | app name, domains, session cookie, REST prefix | Rarely |
| `quora_api_mcp/core/` | `@tool` declaration, errors, the HTTP client with the session (`context.py`) | Yes |
| `quora_api_mcp/session.py` | reading cookies from Chrome over CDP, the session file | Yes |
| `quora_api_mcp/runner.py`, `api.py`, `mcp_server.py`, `mcp_context.py`, `cli.py` | tool registry, REST API, MCP server, its prompts and resources, command line | Yes |
| `examples/` | scripts for common jobs | Yes |

A new tool is a new file in `quora_api_mcp/quora/tools/` with a `@tool(...)` declaration (name, access, input schema, `route`). The registry finds it, and the REST API, the MCP server and the CLI show it without other changes. Quora accepts only the GraphQL operations whose hash it knows: a new one goes into `operations.py`, read from the browser's network panel.

There is no test suite. After a change, run `.venv/bin/quora-mcp tools` and one read tool against the user's account.
