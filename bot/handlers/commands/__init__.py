"""Command handlers — no Telegram dependency.

Each function takes plain Python arguments and returns a string.
The same functions are called by the Telegram dispatcher and by --test mode.
"""

from __future__ import annotations


async def handle_start() -> str:
    return (
        "Welcome to the LMS Bot!\n"
        "I can show you lab analytics and score data.\n"
        "Use /help to see available commands."
    )


async def handle_help() -> str:
    return (
        "Available commands:\n"
        "/start — welcome message\n"
        "/help — show this help\n"
        "/health — check backend status\n"
        "/labs — list available labs\n"
        "/scores <lab-id> — score distribution for a lab (e.g. /scores lab-04)"
    )


async def handle_health() -> str:
    # Task 2: call GET /health on the LMS API
    return "Backend status: not implemented yet (coming in Task 2)"


async def handle_labs() -> str:
    # Task 2: call GET /items/?type=lab on the LMS API
    return "Labs list: not implemented yet (coming in Task 2)"


async def handle_scores(lab_id: str) -> str:
    if not lab_id:
        return "Usage: /scores <lab-id>  (e.g. /scores lab-04)"
    # Task 2: call GET /analytics/scores?lab=<lab_id>
    return f"Scores for {lab_id}: not implemented yet (coming in Task 2)"


async def handle_unknown(text: str) -> str:
    # Task 3: route via LLM intent detection
    return f"Unknown command: {text!r}\nUse /help to see available commands."
