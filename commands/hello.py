from logging import getLogger
from random import choice

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

HELLO_HELP_MESSAGE = "/hello - say hello to the bot"

# TODO Extract to file?
_HELLO_RESPONSES = [
    "Hello there!",
    "Hello!",
    "Hi!",
    "Greetings!",
    "Howdy!",
    "Hey!",
]

_logger = getLogger(__name__)


def hello_command_handler() -> CommandHandler:
    return CommandHandler("hello", _hello)


async def _hello(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    _logger.info(f"[{update.effective_chat.id}] Hello!")
    await update.message.reply_text(choice(_HELLO_RESPONSES))
