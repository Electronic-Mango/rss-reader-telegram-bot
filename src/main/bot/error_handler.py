"""
Module handling all errors within the bot.

It can also detect when chat is deleted and stopped,
after which all data related to this specific chat is deleted.
"""

from logging import getLogger

from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from db.wrapper import remove_stored_chat_data

_logger = getLogger(__name__)


async def handle_errors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    if update is None and context.job is None:
        _logger.error("Unexpected error occured:", exc_info=error)
        return
    chat_id = update.effective_chat.id if update is not None else context.job.chat_id
    _logger.warn(f"[{chat_id}] Error when handling update:", exc_info=error)
    if type(error) is Forbidden:
        _logger.warn(f"[{chat_id}] Cannot send updates to chat, removing chat data")
        remove_stored_chat_data(chat_id)
    else:
        await context.bot.send_message(chat_id, f"Error when handling an update:\n{error}")
