"""
Module handling the "remove" command, allowing users to remove a single subscription.
"""

from logging import getLogger
from typing import Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from bot.user_filter import USER_FILTER
from db.wrapper import chat_has_stored_feeds, get_stored_feed_type_and_name, remove_stored_feed

REMOVE_HELP_MESSAGE = "/remove - remove subscription for a given feed"

_REMOVE_FEED, _CONFIRM = range(2)
_CONFIRM_REMOVAL_YES = "Yes"
_CONFIRM_REMOVAL_NO = "No"
_GO_BACK = "« Back to subscriptions"

_logger = getLogger(__name__)


def remove_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("remove", _handle_remove_request, USER_FILTER)],
        states={
            _REMOVE_FEED: [CallbackQueryHandler(_request_confirmation)],
            _CONFIRM: [
                CallbackQueryHandler(_remove_subscription, lambda data: isinstance(data, tuple)),
                CallbackQueryHandler(_cancel, f"^{_CONFIRM_REMOVAL_NO}$"),
                CallbackQueryHandler(_handle_go_back_to_subscription_list, f"^{_GO_BACK}$"),
            ],
        },
        fallbacks=[CommandHandler("remove", _handle_remove_request, USER_FILTER)],
    )


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled removing subscription")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Cancelled removing subscription")
    return ConversationHandler.END


async def _handle_remove_request(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User requested removal of subscription")
    if chat_has_stored_feeds(chat_id):
        return await _request_feed_to_remove(update.message.reply_text, chat_id)
    else:
        return await _no_feeds_to_remove(update.message, chat_id)


async def _handle_go_back_to_subscription_list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User went back to subscriptions list")
    return await _request_feed_to_remove(query.edit_message_text, chat_id)


async def _request_feed_to_remove(response_callback: Callable, chat_id: int) -> int:
    keyboard = [
        [InlineKeyboardButton(f"{feed_name} ({feed_type})", callback_data=(feed_name, feed_type))]
        for feed_type, feed_name in get_stored_feed_type_and_name(chat_id)
    ]
    await response_callback(
        "Select feed to remove",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return _REMOVE_FEED


async def _no_feeds_to_remove(message: Message, chat_id: int) -> int:
    _logger.info(f"[{chat_id}] No subscriptions to remove")
    await message.reply_text("No subscriptions to remove")
    return ConversationHandler.END


async def _request_confirmation(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    feed_name, feed_type = query.data
    _logger.info(f"[{update.effective_chat.id}] Selected [{feed_name}] [{feed_type}] for removal")
    keyboard = [
        [
            InlineKeyboardButton(_CONFIRM_REMOVAL_YES, callback_data=(feed_name, feed_type)),
            InlineKeyboardButton(_CONFIRM_REMOVAL_NO, callback_data=_CONFIRM_REMOVAL_NO),
        ],
        [InlineKeyboardButton(_GO_BACK, callback_data=_GO_BACK)],
    ]
    await query.edit_message_text(
        f"Confirm removal of <b>{feed_name}</b> ({feed_type})",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return _CONFIRM


async def _remove_subscription(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    feed_name, feed_type = query.data
    _logger.info(f"[{chat_id}] Confirmed [{feed_name}] [{feed_type}] for removal")
    remove_stored_feed(chat_id, feed_type, feed_name)
    await query.edit_message_text(f"Removed subscription for <b>{feed_name}</b>!")
    return ConversationHandler.END
