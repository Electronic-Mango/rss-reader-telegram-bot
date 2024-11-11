"""
Module handling the "start" and "help" commands, printing basic usage and bot description.
Responses for both "start" and "help" are the same.

Description of each command is stored in the module handling this specific command.
"""

from loguru import logger
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.command.add import ADD_HELP_MESSAGE
from bot.command.cancel import CANCEL_HELP_MESSAGE
from bot.command.hello import HELLO_HELP_MESSAGE
from bot.command.remove_all import REMOVE_ALL_HELP_MESSAGE
from bot.command.subs.help import SUBSCRIPTIONS_HELP_MESSAGE
from bot.command.unpin_all import UNPIN_ALL_HELP_MESSAGE
from bot.user_filter import USER_FILTER

HELP_MESSAGES = [
    HELLO_HELP_MESSAGE,
    ADD_HELP_MESSAGE,
    SUBSCRIPTIONS_HELP_MESSAGE,
    REMOVE_ALL_HELP_MESSAGE,
    UNPIN_ALL_HELP_MESSAGE,
    CANCEL_HELP_MESSAGE,
]


def start_help_command_handler() -> CommandHandler:
    return CommandHandler(["start", "help"], _help, USER_FILTER)


async def _help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"[{update.effective_chat.id}] Sending start/help")
    await update.message.reply_text("Simple Web Comics bot based on RSS feeds!")
    await update.message.reply_text("\n".join(HELP_MESSAGES))
