from logging import getLogger

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from commands.add import ADD_HELP_MESSAGE
from commands.hello import HELLO_HELP_MESSAGE
from commands.list import LIST_HELP_MESSAGE
from commands.remove import REMOVE_HELP_MESSAGE
from commands.remove_all import REMOVE_ALL_HELP_MESSAGE

HELP_MESSAGES = [
    HELLO_HELP_MESSAGE,
    LIST_HELP_MESSAGE,
    ADD_HELP_MESSAGE,
    REMOVE_HELP_MESSAGE,
    REMOVE_ALL_HELP_MESSAGE,
]

logger = getLogger(__name__)


def start_help_command_handler():
    return CommandHandler(["start", "help"], help)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Start/help from chat ID=[{update.effective_chat.id}]")
    await update.message.reply_text("Simple Web Comics bot based on RSS feeds!")
    await update.message.reply_text("\n".join(HELP_MESSAGES))
