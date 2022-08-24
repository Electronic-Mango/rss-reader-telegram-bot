"""
Module showing details of a single subscription.
Allows going back to list of specific subscriptions and list of all types.
"""

from datetime import datetime
from logging import getLogger

from dateutil.tz import tzlocal, tzutc
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.command.subs.conversation_state import ConversationState
from bot.command.subs.query_data import NamesData, TypesData, RemoveFeedData
from db.wrapper import get_latest_entry_data

_logger = getLogger(__name__)


async def list_details(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    type, name, chat_data = query.data
    _logger.info(f"[{chat_id}] Showing details for [{type}] [{name}]")
    link, date = get_latest_entry_data(chat_id, type, name)
    await query.edit_message_text(
        _generate_description(type, name, date),
        reply_markup=_prepare_keyboard(type, name, chat_data, link),
    )
    return ConversationState.SHOW_DETAILS


def _generate_description(type: str, name: str, date: list[int]) -> str:
    details = [
        f"Source: <b>{type}</b>",
        f"Name: <b>{name}</b>",
    ]
    if date:
        parsed_date = datetime(*date[:6]).replace(tzinfo=tzutc()).astimezone(tzlocal())
        details.append(f"Updated: <b>{parsed_date.strftime('%Y.%m.%d %H:%M:%S')}</b>")
    return "\n".join(details)


def _prepare_keyboard(
    type: str, name: str, data: dict[str, list[str]], link: str
) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Remove", callback_data=RemoveFeedData(type, name, data))],
        [InlineKeyboardButton("« Back to subscriptions", callback_data=NamesData(type, data))],
        [InlineKeyboardButton("« Back to types", callback_data=TypesData(data))],
    ]
    if link:
        keyboard.insert(0, [InlineKeyboardButton("Latest RSS link", url=link)])
    return InlineKeyboardMarkup(keyboard)
