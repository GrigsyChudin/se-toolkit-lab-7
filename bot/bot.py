"""LMS Telegram Bot entry point.

Usage:
    # Test mode (no Telegram connection needed):
    uv run bot.py --test "/start"
    uv run bot.py --test "/help"
    uv run bot.py --test "/health"
    uv run bot.py --test "/labs"
    uv run bot.py --test "/scores lab-04"

    # Normal mode (starts Telegram polling):
    uv run bot.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from handlers import (
    handle_health,
    handle_help,
    handle_labs,
    handle_scores,
    handle_start,
    handle_unknown,
)


def _parse_test_command(text: str) -> tuple[str, str]:
    """Split '/command args' into (command, args)."""
    parts = text.strip().split(None, 1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return cmd, args


async def _run_test(command_text: str) -> None:
    cmd, args = _parse_test_command(command_text)

    if cmd == "/start":
        response = await handle_start()
    elif cmd == "/help":
        response = await handle_help()
    elif cmd == "/health":
        response = await handle_health()
    elif cmd == "/labs":
        response = await handle_labs()
    elif cmd == "/scores":
        response = await handle_scores(args)
    else:
        response = await handle_unknown(command_text)

    print(response)


async def _run_bot() -> None:
    from aiogram import Bot, Dispatcher
    from aiogram.filters import Command
    from aiogram.types import Message

    from config import settings

    if not settings.bot_token:
        print("ERROR: BOT_TOKEN is not set in .env.bot.secret", file=sys.stderr)
        sys.exit(1)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def on_start(message: Message) -> None:
        await message.answer(await handle_start())

    @dp.message(Command("help"))
    async def on_help(message: Message) -> None:
        await message.answer(await handle_help())

    @dp.message(Command("health"))
    async def on_health(message: Message) -> None:
        await message.answer(await handle_health())

    @dp.message(Command("labs"))
    async def on_labs(message: Message) -> None:
        await message.answer(await handle_labs())

    @dp.message(Command("scores"))
    async def on_scores(message: Message) -> None:
        args = (message.text or "").split(None, 1)
        lab_id = args[1] if len(args) > 1 else ""
        await message.answer(await handle_scores(lab_id))

    @dp.message()
    async def on_unknown(message: Message) -> None:
        await message.answer(await handle_unknown(message.text or ""))

    await dp.start_polling(bot)


def main() -> None:
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        metavar="COMMAND",
        help="Run in test mode: execute COMMAND and print response to stdout",
    )
    args = parser.parse_args()

    if args.test:
        asyncio.run(_run_test(args.test))
        sys.exit(0)

    asyncio.run(_run_bot())


if __name__ == "__main__":
    main()
