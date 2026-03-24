"""LLM client with OpenAI-compatible tool calling loop."""

from __future__ import annotations

import json
import sys

import httpx

from config import settings
from services.lms_client import LMSClient

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_items",
            "description": "Get the full list of labs and tasks from the LMS database",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learners",
            "description": "Get list of enrolled students and their groups",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_scores",
            "description": "Get score distribution histogram (buckets: 0-25, 26-50, 51-75, 76-100) for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pass_rates",
            "description": "Get per-task average scores and attempt counts for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_timeline",
            "description": "Get number of submissions per day for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_groups",
            "description": "Get per-group average scores and student counts for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_learners",
            "description": "Get top N learners by average score for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"},
                    "limit": {"type": "integer", "description": "Number of top learners to return (default 10)"},
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_completion_rate",
            "description": "Get completion rate (percentage of learners who scored >= 60) for a lab",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab": {"type": "string", "description": "Lab identifier, e.g. 'lab-01'"}
                },
                "required": ["lab"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_sync",
            "description": "Refresh data from the autochecker API (runs the ETL pipeline sync)",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

SYSTEM_PROMPT = """You are an LMS analytics assistant. You help users explore lab data and student performance.
Use the provided tools to fetch data and answer questions. Always use tools to get real data — never make up numbers.
If the user asks about a specific lab, use its identifier (e.g. lab-01, lab-02, ..., lab-07).
When the user message is ambiguous, ask a clarifying question or show what you can do.
Keep answers concise and informative."""


async def _call_tool(name: str, args: dict) -> str:
    lms = LMSClient()
    try:
        if name == "get_items":
            result = await lms.get_items()
        elif name == "get_learners":
            result = await lms.get_learners()
        elif name == "get_scores":
            result = await lms.get_scores(args["lab"])
        elif name == "get_pass_rates":
            result = await lms.get_pass_rates(args["lab"])
        elif name == "get_timeline":
            result = await lms.get_timeline(args["lab"])
        elif name == "get_groups":
            result = await lms.get_groups(args["lab"])
        elif name == "get_top_learners":
            result = await lms.get_top_learners(args["lab"], args.get("limit", 10))
        elif name == "get_completion_rate":
            result = await lms.get_completion_rate(args["lab"])
        elif name == "trigger_sync":
            result = await lms.trigger_sync()
        else:
            return f"Unknown tool: {name}"

        summary = f"{len(result)} items" if isinstance(result, list) else str(result)[:100]
        print(f"[tool] Result: {summary}", file=sys.stderr)
        return json.dumps(result)
    except Exception as e:
        return f"Error calling {name}: {e}"


async def route(user_message: str) -> str:
    """Route a free-text message through the LLM tool calling loop."""
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    base_url = settings.llm_api_base_url.rstrip("/")
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    for _ in range(10):  # max iterations
        payload = {
            "model": settings.llm_api_model,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
        }

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                r = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
            except httpx.HTTPError as e:
                return f"LLM error: {e}"

        data = r.json()
        choice = data["choices"][0]
        msg = choice["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return msg.get("content") or "No response from LLM."

        # Execute all tool calls and feed results back
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"].get("arguments", "{}"))
            print(f"[tool] LLM called: {fn_name}({fn_args})", file=sys.stderr)
            result = await _call_tool(fn_name, fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

        print(f"[summary] Feeding {len(tool_calls)} tool result(s) back to LLM", file=sys.stderr)

    return "Reached maximum reasoning steps. Please try a simpler question."
