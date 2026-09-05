"""
Module handling printing feed names from selected type.

Also allows going back to the list of all types.
"""

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.query_data import DetailsData, TypesData


async def list_names(update: Update, _: ContextTypes.DEFAULT_TYPE) -> ConversationState:
    query = update.callback_query
    await query.answer()
    feed_type, chat_data = query.data
    logger.info(f"[{update.effective_chat.id}] Requesting feed name for [{feed_type}]")
    await query.edit_message_text(
        "Select subscription:",
        reply_markup=_prepare_keyboard(feed_type, chat_data),
    )
    return ConversationState.LIST_NAMES


def _prepare_keyboard(feed_type: str, chat_data: dict[str, list[str]]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(name, callback_data=DetailsData(feed_type, name, chat_data))]
        for name in chat_data[feed_type]
    ]
    keyboard += [[InlineKeyboardButton("« Back to types", callback_data=TypesData(chat_data))]]
    return InlineKeyboardMarkup(keyboard)
