"""
Module handling subscription removal from the details view.
"""

from logging import getLogger

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.query_data import DetailsData, NamesData, TypesData
from db.wrapper import remove_stored_feed

_logger = getLogger(__name__)


async def request_confirmation(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """Request confirmation for removal of selected subscription"""
    query = update.callback_query
    await query.answer()
    type, name, chat_data = query.data
    _logger.info(f"[{update.effective_chat.id}] Selected [{type}] [{name}] for removal")
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data=query.data),
            InlineKeyboardButton("No", callback_data=DetailsData(type, name, chat_data)),
        ],
        [InlineKeyboardButton("« Back to subscriptions", callback_data=NamesData(type, chat_data))],
        [InlineKeyboardButton("« Back to types", callback_data=TypesData(chat_data))],
    ]
    await query.edit_message_text(
        f"Confirm removal of <b>{name}</b> ({type})",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return ConversationState.CONFIRM_REMOVAL


async def remove_subscription(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """Remove selected subscription"""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    feed_type, feed_name, _ = query.data
    _logger.info(f"[{chat_id}] Confirmed [{feed_name}] [{feed_type}] for removal")
    remove_stored_feed(chat_id, feed_type, feed_name)
    await query.edit_message_text(f"Removed subscription for <b>{feed_name}</b>!")
    return ConversationHandler.END
