"""
Module showing details of a single subscription.
Allows going back to list of specific subscriptions and list of all types.
"""

from logging import getLogger

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.query_data import NamesData, TypesData, RemoveFeedData

_logger = getLogger(__name__)


async def list_details(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    type, name, chat_data = query.data
    _logger.info(f"[{update.effective_chat.id}] Showing details for [{type}] [{name}]")
    await query.edit_message_text(
        _generate_description(type, name),
        reply_markup=_prepare_keyboard(type, name, chat_data),
    )
    return ConversationState.SHOW_DETAILS


def _generate_description(type: str, name: str) -> str:
    details = [f"Subscription type:<b>{type}</b>", f"Subscription name:<b>{name}</b>"]
    return "\n".join(details)


def _prepare_keyboard(type: str, name: str, data: dict[str, list[str]]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Remove", callback_data=RemoveFeedData(type, name, data))],
        [InlineKeyboardButton("« Back to subscriptions", callback_data=NamesData(type, data))],
        [InlineKeyboardButton("« Back to types", callback_data=TypesData(data))],
    ]
    return InlineKeyboardMarkup(keyboard)
