"""
Module handling the "hello" command, mostly used for simple debugging purposes.
Bot always responds with "Hello there!" and that's it.
"""

from loguru import logger
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.user_filter import USER_FILTER

HELLO_HELP_MESSAGE = "/hello - say hello to the bot"


def hello_command_handler() -> CommandHandler:
    return CommandHandler("hello", _hello, USER_FILTER)


async def _hello(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"[{update.effective_chat.id}] Hello!")
    await update.message.reply_text("Hello there!")
