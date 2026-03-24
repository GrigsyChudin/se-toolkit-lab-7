# Bot Development Plan

## Overview

This project implements a Telegram bot that acts as a conversational interface
to the LMS backend API. The bot provides lab analytics, score data, and learner
statistics directly in Telegram chat.

## Architecture

The bot follows a layered architecture with testable handlers at its core:

- **Handlers** (`handlers/`) — pure async functions that accept typed inputs and
  return plain text. They have no dependency on Telegram or aiogram, which means
  they can be called directly in `--test` mode and in unit tests.
- **Services** (`services/`) — thin HTTP clients wrapping the LMS API and LLM API.
  Handlers call services; services call the network.
- **Config** (`config.py`) — all environment variables loaded once at startup
  using `pydantic-settings`. Both `--test` mode and the real bot share the same
  config, sourced from `.env.bot.secret`.
- **Entry point** (`bot.py`) — wires everything together. With `--test` flag it
  dispatches the command string directly to the matching handler and prints the
  result to stdout. Without the flag it starts the aiogram Telegram bot.

## Task breakdown

### Task 1 — Scaffold (this task)
Create the project skeleton: `pyproject.toml`, `config.py`, handler stubs,
service stubs, and working `--test` mode. Verify offline with
`uv run bot.py --test "/start"`.

### Task 2 — Backend integration
Implement real handler logic by calling LMS API endpoints:
`/items/` (labs list), `/analytics/scores`, `/analytics/group-performance`,
`/health`. Format responses as readable Telegram messages.

### Task 3 — Intent routing
Add free-text message handling. Route user messages to the correct handler using
an LLM call (Qwen via `LLM_API_BASE_URL`). Implement a simple system prompt that
maps intent to command.

### Task 4 — Deployment
Run the bot as a background process on the VM using `nohup`. Document the
`pkill / nohup` deploy pattern. Verify end-to-end in Telegram.

## Key decisions

- Use `uv` for dependency management; no `requirements.txt`.
- `pydantic-settings` for config to get automatic validation and type coercion.
- `httpx` (async) for HTTP calls — same library used in the backend.
- `aiogram` v3 for Telegram transport.
- Handlers are sync-free where possible; async only when calling I/O.
