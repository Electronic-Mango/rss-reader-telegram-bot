"""
Module handling the "removeall" command, allowing users delete all subscriptions.
"""

from logging import getLogger

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from bot.user_filter import USER_FILTER
from db.wrapper import chat_has_stored_feeds, remove_stored_chat_data

REMOVE_ALL_HELP_MESSAGE = "/removeall - remove all subscriptions"

_CONFIRM_1, _CONFIRM_2 = range(2)
_CONFIRM_1_YES = "Yes"
_CONFIRM_1_NO = "No"
_CONFIRM_2_YES = "Yes, I'm sure"
_CONFIRM_2_NO = "No, don't remove"

_logger = getLogger(__name__)


def remove_all_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("removeall", _request_confirmation_1, USER_FILTER)],
        states={
            _CONFIRM_1: [
                CallbackQueryHandler(_request_confirmation_2, f"^{_CONFIRM_1_YES}$"),
                CallbackQueryHandler(_cancel, f"^{_CONFIRM_1_NO}$"),
            ],
            _CONFIRM_2: [
                CallbackQueryHandler(_remove_all_subscriptions, f"^{_CONFIRM_2_YES}$"),
                CallbackQueryHandler(_cancel, f"^{_CONFIRM_2_NO}$"),
            ],
        },
        fallbacks=[CommandHandler("removeall", _request_confirmation_1, USER_FILTER)],
    )


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled removing subscriptions")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Cancelled removing all subscriptions")
    return ConversationHandler.END


async def _request_confirmation_1(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User requested removal of all subscriptions")
    if not chat_has_stored_feeds(chat_id):
        return await _no_feeds_to_remove(update.message, chat_id)
    await update.message.reply_text(
        "Confirm removal of all feeds",
        reply_markup=_prepare_keyboard(_CONFIRM_1_YES, _CONFIRM_1_NO),
    )
    return _CONFIRM_1


async def _request_confirmation_2(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Are you sure you want to remove <b>all</b> subscriptions?",
        reply_markup=_prepare_keyboard(_CONFIRM_2_NO, _CONFIRM_2_YES),
    )
    return _CONFIRM_2


async def _remove_all_subscriptions(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Removing all subscriptions")
    remove_stored_chat_data(chat_id)
    await query.edit_message_text("Removed all subscriptions")
    return ConversationHandler.END


async def _no_feeds_to_remove(message: Message, chat_id: int) -> int:
    _logger.info(f"[{chat_id}] No subscriptions to remove")
    await message.reply_text("No subscriptions to remove")
    return ConversationHandler.END


def _prepare_keyboard(*data: str) -> InlineKeyboardMarkup:
    keyboard = map(lambda data: InlineKeyboardButton(data, callback_data=data), data)
    return InlineKeyboardMarkup([list(keyboard)])
