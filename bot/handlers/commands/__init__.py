"""Command handlers — no Telegram dependency.

Each function returns a plain string.
Called by --test mode and by the Telegram dispatcher.
"""

from __future__ import annotations

import httpx

from services.lms_client import LMSClient


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
    client = LMSClient()
    try:
        items = await client.get_items()
        return f"Backend: OK — {len(items)} items in database"
    except httpx.HTTPError as e:
        return f"Backend: unreachable ({e})"
    except Exception as e:
        return f"Backend: error ({e})"


async def handle_labs() -> str:
    client = LMSClient()
    try:
        items = await client.get_items()
        labs = [x for x in items if x.get("type") == "lab"]
        if not labs:
            return "No labs found in the database."
        lines = ["Available labs:"]
        for lab in sorted(labs, key=lambda x: x["title"]):
            lines.append(f"  • {lab['title']}")
        return "\n".join(lines)
    except httpx.HTTPError as e:
        return f"Could not fetch labs: {e}"
    except Exception as e:
        return f"Error: {e}"


async def handle_scores(lab_id: str) -> str:
    if not lab_id:
        return "Usage: /scores <lab-id>  (e.g. /scores lab-04)"
    client = LMSClient()
    try:
        rows = await client.get_pass_rates(lab_id)
        if not rows:
            return f"No data found for {lab_id}. Check the lab ID (e.g. lab-01)."
        lines = [f"Scores for {lab_id}:"]
        for row in rows:
            task = row.get("task", "Unknown task")
            avg = row.get("avg_score", 0)
            attempts = row.get("attempts", 0)
            lines.append(f"  • {task}: {avg:.1f}% avg, {attempts} attempts")
        return "\n".join(lines)
    except httpx.HTTPError as e:
        return f"Could not fetch scores: {e}"
    except Exception as e:
        return f"Error: {e}"


async def handle_unknown(text: str) -> str:
    # Task 3: route via LLM intent detection
    return f"Unknown command: {text!r}\nUse /help to see available commands."
