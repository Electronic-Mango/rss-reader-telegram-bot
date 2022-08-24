"""
Module handling listing subscribed feed types.
"""

from logging import getLogger
from typing import Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.query_data import NamesData
from db.wrapper import get_stored_feed_type_to_names

_logger = getLogger(__name__)


async def initial_list_feed_types(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Initial list of types directly after "subscriptions" command is run"""
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Initial request of feed type")
    chat_data = get_stored_feed_type_to_names(chat_id)
    await _send_types_list(update.message.reply_text, chat_data)


async def followup_list_feed_types(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """List of types after going back from list of names"""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Followup request of feed type")
    await _send_types_list(query.edit_message_text, query.data.chat_data)
    return ConversationState.LIST_TYPES


async def _send_types_list(response_callback: Callable, chat_data: dict[str, list[str]]) -> None:
    keyboard = [
        [InlineKeyboardButton(type, callback_data=NamesData(type, chat_data))]
        for type in chat_data.keys()
    ]
    await response_callback(
        "Select subscription type:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
