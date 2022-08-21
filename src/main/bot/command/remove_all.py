"""
Module handling the "removeall" command, allowing users delete all subscriptions.
"""

from collections import namedtuple
from logging import getLogger
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from bot.user_filter import USER_FILTER
from db.wrapper import chat_has_stored_feeds, remove_stored_chat_data

REMOVE_ALL_HELP_MESSAGE = "/removeall - remove all subscriptions"

_CONFIRM_2_STATE = range(1)
_CONFIRM_1_YES = "Yes"
_CONFIRM_1_NO = "No"
_CONFIRM_2_YES = "Yes, I'm sure"
_CONFIRM_2_NO = "No, don't remove"

_RemoveAllData = namedtuple("RemoveAll", ["cnf"])
_logger = getLogger(__name__)


def remove_all_initial_handler() -> CommandHandler:
    return CommandHandler("removeall", _request_confirmation_1, USER_FILTER)


def remove_all_followup_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(_request_confirmation_2, _data_confirmed),
            CallbackQueryHandler(_cancel, _data_not_confirmed),
        ],
        states={
            _CONFIRM_2_STATE: [
                CallbackQueryHandler(_remove_all_subscriptions, _data_confirmed),
                CallbackQueryHandler(_cancel, _data_not_confirmed),
            ],
        },
        fallbacks=[CallbackQueryHandler(_cancel)],
        per_message=True,
    )


def _data_confirmed(data: Any) -> bool:
    return isinstance(data, _RemoveAllData) and data.cnf


def _data_not_confirmed(data: Any) -> bool:
    return isinstance(data, _RemoveAllData) and not data.cnf


async def _request_confirmation_1(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User requested removal of all subscriptions")
    if not chat_has_stored_feeds(chat_id):
        _logger.info(f"[{chat_id}] No subscriptions to remove")
        await update.message.reply_text("No subscriptions to remove")
    else:
        await update.message.reply_text(
            "Do you want to remove all subscriptions?",
            reply_markup=_prepare_keyboard((_CONFIRM_1_YES, True), (_CONFIRM_1_NO, False)),
        )


async def _request_confirmation_2(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Are you sure you want to remove <b>all</b> subscriptions?",
        reply_markup=_prepare_keyboard((_CONFIRM_2_NO, False), (_CONFIRM_2_YES, True)),
    )
    return _CONFIRM_2_STATE


async def _remove_all_subscriptions(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Removing all subscriptions")
    remove_stored_chat_data(chat_id)
    await query.edit_message_text("Removed all subscriptions")
    return ConversationHandler.END


def _prepare_keyboard(*keyboard_data: tuple[str, bool]) -> InlineKeyboardMarkup:
    keyboard = [[_prepare_keyboard_button(name, cnf) for name, cnf in keyboard_data]]
    return InlineKeyboardMarkup(keyboard)


def _prepare_keyboard_button(name: str, cnf: bool) -> InlineKeyboardButton:
    return InlineKeyboardButton(name, callback_data=_RemoveAllData(cnf))


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled removing subscriptions")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("No subscriptions have beed removed")
    return ConversationHandler.END
