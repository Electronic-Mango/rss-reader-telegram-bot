from logging import getLogger

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from telegram.ext.filters import COMMAND, TEXT

from db import chat_has_feeds
from error_handler import stop_jobs_and_remove_data

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
    if not chat_has_feeds(chat_id):
        _logger.info(f"[{chat_id}] No subscriptions to remove")
        await update.message.reply_text("No subscriptions to remove")
        return ConversationHandler.END
    confirmation_keyboard = [[_CONFIRM_1_YES, "No"]]
    await update.message.reply_text(
        "Confirm removal of all feeds",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=confirmation_keyboard,
            # Intentionally is not a one time keyboard.
            # Confirming removal will trigger a second keyboard, which is one time.
            # Cancellation will hide the keyboard.
            resize_keyboard=True,
            input_field_placeholder="Confirm removal",
        ),
    )
    return _CONFIRM_1


async def _request_confirmation_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    confirmation_1 = update.message.text
    if confirmation_1 != _CONFIRM_1_YES:
        return await _cancel(update, context)
    _logger.info(f"[{update.effective_chat.id}] User send first confirmation")
    confirmation_keyboard = [[_CONFIRM_2_YES, "No, don't remove"]]
    await update.message.reply_text(
        "Are you sure you want to remove <b>all</b> subscriptions?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=confirmation_keyboard,
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
    stop_jobs_and_remove_data(context.job_queue, chat_id)
    await update.message.reply_text("Removed all subscriptions")
    return ConversationHandler.END
