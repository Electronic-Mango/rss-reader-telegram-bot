"""
Module handling all errors within the bot.

It can also detect when chat is deleted and stopped,
after which all data related to this specific chat is deleted.
"""

from logging import getLogger

from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from bot.sender import send_update
from db.wrapper import remove_stored_chat_data

_logger = getLogger(__name__)


async def handle_errors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update is None and context.job is None:
        _logger.error("Unexpected error occured:", exc_info=context.error)
    elif update:
        await _handle_update_error(update, context)
    else:
        await _handle_job_error(context)


async def _handle_update_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    error = context.error
    _logger.warn(f"[{chat_id}] Error when handling update:", exc_info=error)
    if type(error) is Forbidden and chat_id:
        await _handle_forbidden_error(chat_id)
    elif chat_id:
        await context.bot.send_message(chat_id, f"Error when handling an update:\n{error}")


async def _handle_job_error(context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    chat_id, feed_type, feed_name, link, title, description = context.job.data
    context.job.data = chat_id
    _logger.warn(f"[{chat_id}] Error in job:", exc_info=error)
    if type(error) is Forbidden:
        await _handle_forbidden_error(chat_id)
    else:
        _logger.warn(f"[{chat_id}] Trying to resend data without media")
        description = f"<b>Error when sending original update: {error}</b>\n\n{description}"
        await send_update(context.bot, chat_id, feed_type, feed_name, link, title, description)


async def _handle_forbidden_error(chat_id: int) -> None:
    _logger.warn(f"[{chat_id}] Cannot send updates to chat, removing chat data")
    remove_stored_chat_data(chat_id)
