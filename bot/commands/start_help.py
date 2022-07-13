# TODO Perhaps add a detailed help view for each command?

from logging import getLogger

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.commands.add import ADD_HELP_MESSAGE
from bot.commands.hello import HELLO_HELP_MESSAGE
from bot.commands.list import LIST_HELP_MESSAGE
from bot.commands.remove import REMOVE_HELP_MESSAGE
from bot.commands.remove_all import REMOVE_ALL_HELP_MESSAGE

HELP_MESSAGES = [
    HELLO_HELP_MESSAGE,
    LIST_HELP_MESSAGE,
    ADD_HELP_MESSAGE,
    REMOVE_HELP_MESSAGE,
    REMOVE_ALL_HELP_MESSAGE,
]

logger = getLogger(__name__)


def start_help_command_handler() -> CommandHandler:
    return CommandHandler(["start", "help"], _help)


async def _help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"[{update.effective_chat.id}] Sending start/help")
    await update.message.reply_text("Simple Web Comics bot based on RSS feeds!")
    await update.message.reply_text("\n".join(HELP_MESSAGES))
