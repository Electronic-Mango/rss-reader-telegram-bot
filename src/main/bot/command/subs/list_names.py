"""
Module handling printing feed names from selected type.
Also allows going back to the list of all types.
"""

from logging import getLogger

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.query_data import DetailsData, TypesData

_logger = getLogger(__name__)


async def list_names(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    type, chat_data = query.data
    _logger.info(f"[{update.effective_chat.id}] Requesting feed name for [{type}]")
    # TODO Should names be loaded from the DB instead?
    await query.edit_message_text(
        "Select specific subscription:",
        reply_markup=_prepare_keyboard(type, chat_data),
    )
    return ConversationState.LIST_NAMES


def _prepare_keyboard(type: str, chat_data: dict[str, list[str]]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(name, callback_data=DetailsData(type, name, chat_data))]
        for name in chat_data[type]
    ]
    keyboard += [[InlineKeyboardButton("« Back to types", callback_data=TypesData(chat_data))]]
    return InlineKeyboardMarkup(keyboard)
