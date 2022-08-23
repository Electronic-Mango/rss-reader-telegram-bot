from logging import getLogger

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.command.list.conversation_state import State
from bot.command.list.query_data import ListTypesData

_logger = getLogger(__name__)


async def list_names(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    type, names, chat_data = query.data
    _logger.info(f"[{update.effective_chat.id}] Listing all feed names for [{type}]")
    # TODO Should names be loaded from the DB instead?
    keyboard = [[InlineKeyboardButton("« Back to types", callback_data=ListTypesData(chat_data))]]
    names_message = "\n".join(map(_prepare_name, sorted(names)))
    await query.edit_message_text(
        f"Your <b>{type}</b> subscriptions:\n{names_message}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return State.LIST_NAMES


def _prepare_name(name: str) -> str:
    return f"<b>{name}</b>"
