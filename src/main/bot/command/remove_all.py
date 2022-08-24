"""
Module handling the "removeall" command, allowing users delete all subscriptions.
"""

from enum import Enum, auto
from logging import getLogger
from typing import Any, NamedTuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from bot.user_filter import USER_FILTER
from db.wrapper import chat_has_stored_feeds, remove_stored_chat_data

REMOVE_ALL_HELP_MESSAGE = "/removeall - remove all subscriptions"


class _ConversationState(Enum):
    CONFIRM_2 = auto()


class _RemoveAllData(NamedTuple):
    cnf: bool


_logger = getLogger(__name__)


def remove_all_initial_handler() -> CommandHandler:
    return CommandHandler("removeall", _request_confirmation_1, USER_FILTER)


def remove_all_followup_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(_request_confirmation_2, _data_confirmed),
            CallbackQueryHandler(_cancel, _data_rejected),
        ],
        states={
            _ConversationState.CONFIRM_2: [
                CallbackQueryHandler(_remove_all_subscriptions, _data_confirmed),
                CallbackQueryHandler(_cancel, _data_rejected),
            ],
        },
        fallbacks=[CallbackQueryHandler(_cancel)],
        per_message=True,
        name="remove_all_followup_handler",
        persistent=True,
    )


def _data_confirmed(data: Any) -> bool:
    return isinstance(data, _RemoveAllData) and data.cnf


def _data_rejected(data: Any) -> bool:
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
            reply_markup=_prepare_keyboard(("Yes", True), ("No", False)),
        )


async def _request_confirmation_2(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Are you sure you want to remove <b>all</b> subscriptions?",
        reply_markup=_prepare_keyboard(("No, don't remove", False), ("Yes, I'm sure", True)),
    )
    return _ConversationState.CONFIRM_2


async def _remove_all_subscriptions(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Removing all subscriptions")
    remove_stored_chat_data(chat_id)
    await query.edit_message_text("Removed all subscriptions")
    return ConversationHandler.END


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled removing subscriptions")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("No subscriptions have beed removed")
    return ConversationHandler.END


def _prepare_keyboard(*keyboard_data: tuple[str, bool]) -> InlineKeyboardMarkup:
    keyboard = [[_prepare_keyboard_button(name, cnf) for name, cnf in keyboard_data]]
    return InlineKeyboardMarkup(keyboard)


def _prepare_keyboard_button(name: str, cnf: bool) -> InlineKeyboardButton:
    return InlineKeyboardButton(name, callback_data=_RemoveAllData(cnf))
