from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from commands.add import ADD_HELP_MESSAGE
from commands.hello import HELLO_HELP_MESSAGE
from commands.list import LIST_HELP_MESSAGE
from commands.remove import REMOVE_HELP_MESSAGE
from commands.start import START_HELP_MESSAGE

HELP_HELP_MESSAGE = "/help - prints this help message"
HELP_MESSAGES = [
    START_HELP_MESSAGE,
    HELLO_HELP_MESSAGE,
    LIST_HELP_MESSAGE,
    ADD_HELP_MESSAGE,
    REMOVE_HELP_MESSAGE,
    HELP_HELP_MESSAGE,
]


def help_command_handler():
    return CommandHandler("help", help)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Help from chat ID=[{update.effective_chat.id}]")

    await update.message.reply_text("\n".join(HELP_MESSAGES))

