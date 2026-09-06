from __future__ import annotations

import asyncio
import logging
import os

from telegram.ext import ApplicationBuilder

from src.bot.telegram_bot import build_bot


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    application = build_bot()
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
