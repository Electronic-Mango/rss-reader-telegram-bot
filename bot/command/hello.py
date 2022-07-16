"""
Module handling the "hello" command, mostly used for simple debugging purposes.
Bot always responds with "Hello there!" and that's it.
"""

from logging import getLogger

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

HELLO_HELP_MESSAGE = "/hello - say hello to the bot"

_logger = getLogger(__name__)


def hello_command_handler() -> CommandHandler:
    return CommandHandler("hello", _hello)


async def _hello(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    _logger.info(f"[{update.effective_chat.id}] Hello!")
    await update.message.reply_text("Hello there!")
