# TODO Allow removing feed via a single command, rather than a conversation

from logging import getLogger
from re import match

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler, MessageHandler
from telegram.ext.filters import COMMAND, TEXT

from db import chat_has_stored_feeds, get_stored_feed_type_and_name, remove_stored_feed

REMOVE_HELP_MESSAGE = "/remove - remove subscription for a given feed"

_CONFIRM_REMOVAL_YES = "Yes"
_REMOVE_FEED, _CONFIRM = range(2)

_logger = getLogger(__name__)


def remove_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("remove", _request_feed_name)],
        states={
            _REMOVE_FEED: [MessageHandler(TEXT & ~COMMAND, _confirm_removal)],
            _CONFIRM: [MessageHandler(TEXT & ~COMMAND, _remove_subscription)],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
    )


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled removing subscription")
    await update.message.reply_text(
        "Cancelled removing subscription", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def _request_feed_name(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User requested removal of subscription")
    if not chat_has_stored_feeds(chat_id):
        _logger.info(f"[{chat_id}] No subscriptions to remove")
        await update.message.reply_text("No subscriptions to remove")
        return ConversationHandler.END
    all_feed_names = [
        [f"{feed_name} ({feed_type})"]
        for feed_type, feed_name in get_stored_feed_type_and_name(chat_id)
    ]
    await update.message.reply_text(
        "Select feed to remove, or /cancel",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=all_feed_names,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Select feed to remove",
        ),
    )
    return _REMOVE_FEED


async def _confirm_removal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard_message = update.message.text
    feed_name, feed_type = _feed_name_and_type_from_keyboard_message(keyboard_message)
    _logger.info(f"[{update.effective_chat.id}] Selected [{feed_name}] [{feed_type}] for removal")
    context.user_data[_REMOVE_FEED] = (feed_type, feed_name)
    confirmation_keyboard = [[_CONFIRM_REMOVAL_YES, "No"]]
    await update.message.reply_text(
        f"Confirm removal of <b>{feed_name}</b> ({feed_type})",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=confirmation_keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Confirm removal",
        ),
    )
    return _CONFIRM


async def _remove_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    confirmation = update.message.text
    if confirmation != _CONFIRM_REMOVAL_YES:
        return await _cancel(update, context)
    chat_id = update.effective_chat.id
    feed_type, feed_name = context.user_data[_REMOVE_FEED]
    _logger.info(f"[{chat_id}] Confirmed [{feed_name}] [{feed_type}] for removal")
    remove_stored_feed(chat_id, feed_type, feed_name)
    await update.message.reply_text(
        f"Removed subscription for <b>{feed_name}</b>!", parse_mode="HTML"
    )
    return ConversationHandler.END


def _feed_name_and_type_from_keyboard_message(keyboard_message: str) -> tuple[str, str]:
    _logger.info(keyboard_message)
    keyboard_message_pattern = r"(.+)+ \((.+)\)"
    keyboard_message_match = match(keyboard_message_pattern, keyboard_message)
    return keyboard_message_match.groups()
