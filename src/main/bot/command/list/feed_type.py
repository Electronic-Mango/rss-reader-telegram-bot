"""
Module handling listing available feed types.
"""

from logging import getLogger
from typing import Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.command.list.conversation_state import State
from bot.command.list.query_data import ListNamesData
from db.wrapper import get_stored_feed_type_to_names

_logger = getLogger(__name__)


async def initial_list_feed_types(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Initial list of types directly after "list" command is run"""
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Initial request of feed type")
    chat_data = get_stored_feed_type_to_names(chat_id)
    await _send_types_list(update.message.reply_text, chat_data)


async def followup_list_feed_types(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to the list of types from the list of names"""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Followup request of feed type")
    await _send_types_list(query.edit_message_text, *query.data)
    return State.LIST_TYPES


async def _send_types_list(response_callback: Callable, chat_data: dict[str, list[str]]) -> None:
    keyboard = [
        [InlineKeyboardButton(type, callback_data=ListNamesData(type, names, chat_data))]
        for type, names in chat_data.items()
    ]
    await response_callback(
        "Select subscription type",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
