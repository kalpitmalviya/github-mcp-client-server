# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

MCP Chat: a command-line chat client for the Anthropic API that demonstrates the MCP (Model Context Protocol) architecture. It has document retrieval (`@doc_id` mentions), MCP server-defined slash commands/prompts (`/command doc_id`), and tool-calling via one or more MCP servers.

## Running the project

Environment variables live in `.env` (not committed): `ANTHROPIC_API_KEY`, `CLAUDE_MODEL`, and `USE_UV` (1 if using uv to launch `mcp_server.py`, 0 if using `python`).

```bash
uv run main.py          # with uv
python main.py          # without uv (make sure USE_UV=0)
```

Additional MCP server scripts can be passed as CLI args (`main.py other_server.py`); each is launched with `uv run <script>` and registered as its own client.

There are no lint, type-check, or test commands configured in this repo (per README).

## Architecture

Two processes talk over MCP via stdio: the CLI chat app (this repo's main process) and `mcp_server.py` (a FastMCP server), connected through `mcp_client.py`'s `MCPClient`. `main.py` always spins up a `doc_client` connection to `mcp_server.py`, plus one `MCPClient` per extra server script passed on the command line, all held in an `AsyncExitStack` and passed to `CliChat` as a `clients` dict.

Request flow for a user turn:
1. `core/cli.py` (`CliApp`) reads input from a `prompt_toolkit` session (with `@doc` and `/command` autocomplete) and calls `agent.run(user_input)`.
2. `core/cli_chat.py` (`CliChat`, subclass of `core/chat.py`'s `Chat`) overrides `_process_query`: if the input starts with `/`, it treats it as an MCP prompt (`doc_client.get_prompt`) and injects the returned prompt messages directly into history; otherwise it scans for `@doc_id` mentions, resolves them via MCP resources (`docs://documents`, `docs://documents/{doc_id}`), and wraps the query plus fetched doc content into an instructional prompt appended to `self.messages`.
3. `Chat.run` then loops: call `Claude.chat(messages, tools=...)`, append the assistant response, and if `stop_reason == "tool_use"`, dispatch tool calls via `core/tools.py`'s `ToolManager.execute_tool_requests` (which finds the right MCP client for each requested tool name and calls it), appends the tool results as a user message, and loops again. The loop ends when Claude returns a non-tool-use response.
4. `core/claude.py` (`Claude`) is a thin wrapper around the `anthropic` SDK's `messages.create`, plus helpers for appending user/assistant messages in Anthropic's message-param shape and extracting text from a response.

On the server side, `mcp_server.py` defines an in-memory `docs` dict (doc_id -> content) exposed via:
- Tools: `read_doc_content`, `edit_doc_content`.
- Resources: `docs://documents` (list of IDs), `docs://documents/{doc_id}` (content of one doc).
- Prompts: e.g. `formatt` (rewrite a doc as markdown) — these become the `/command doc_id` slash commands in the CLI, and are fetched via `MCPClient.get_prompt` / `list_prompts`.

`core/cli.py` also contains a fair amount of `prompt_toolkit` completion/key-binding logic (`UnifiedCompleter`, `CommandAutoSuggest`) that drives `@` and `/` tab-completion against the live list of resources/prompts fetched from the doc server at startup (`CliApp.initialize` -> `refresh_resources`/`refresh_prompts`).

Adding a new document: edit the `docs` dict in `mcp_server.py`. Adding a new MCP tool/resource/prompt: add it in `mcp_server.py` using the `@mcp.tool`/`@mcp.resource`/`@mcp.prompt` decorators; no client-side registration is needed since tools/prompts/resources are discovered dynamically at runtime.