"""
Module handling the "removeall" command, allowing users delete all subscriptions.
"""

from logging import getLogger

from telegram import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from telegram.ext.filters import COMMAND, TEXT

from db.wrapper import chat_has_stored_feeds, remove_stored_chat_data

REMOVE_ALL_HELP_MESSAGE = "/removeall - remove all subscriptions"

_CONFIRM_1, _CONFIRM_2 = range(2)
_CONFIRM_1_YES = "Yes"
_CONFIRM_2_YES = "Yes, I'm sure"

_logger = getLogger(__name__)


def remove_all_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("removeall", _request_confirmation_1)],
        states={
            _CONFIRM_1: [MessageHandler(TEXT & ~COMMAND, _request_confirmation_2)],
            _CONFIRM_2: [MessageHandler(TEXT & ~COMMAND, _remove_all)],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
    )


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled removing subscriptions")
    await update.message.reply_text(
        "Cancelled removing all subscriptions", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def _request_confirmation_1(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User requested removal of all subscriptions")
    if not chat_has_stored_feeds(chat_id):
        await _no_feeds_to_remove(update.message, chat_id)
        return
    await update.message.reply_text(
        "Confirm removal of all feeds",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[_CONFIRM_1_YES, "No"]],
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Confirm removal",
        ),
    )
    return _CONFIRM_1


async def _no_feeds_to_remove(message: Message, chat_id: int) -> int:
    _logger.info(f"[{chat_id}] No subscriptions to remove")
    await message.reply_text("No subscriptions to remove")
    return ConversationHandler.END


async def _request_confirmation_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    confirmation_1 = update.message.text
    if confirmation_1 != _CONFIRM_1_YES:
        return await _cancel(update, context)
    _logger.info(f"[{update.effective_chat.id}] User send first confirmation")
    await update.message.reply_text(
        "Are you sure you want to remove <b>all</b> subscriptions?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[["No, don't remove", _CONFIRM_2_YES]],
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Confirm removal",
        ),
    )
    return _CONFIRM_2


async def _remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    confirmation_2 = update.message.text
    if confirmation_2 != _CONFIRM_2_YES:
        return await _cancel(update, context)
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] Removing all subscriptions")
    remove_stored_chat_data(chat_id)
    await update.message.reply_text("Removed all subscriptions")
    return ConversationHandler.END
