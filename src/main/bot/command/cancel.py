"""
Module handling the default response for "cancel" command.

Normally, "cancel" command is send to stop a conversation-style command,
here it's just informing the user, that there are no operations to cancel.
"""

from loguru import logger
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bot.user_filter import USER_FILTER

CANCEL_HELP_MESSAGE = "/cancel - cancel the current operation"


def cancel_command_handler() -> CommandHandler:
    return CommandHandler("cancel", _cancel, USER_FILTER)


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"[{update.effective_chat.id}] No operation to cancel")
    await update.message.reply_text("No active operation to cancel")
