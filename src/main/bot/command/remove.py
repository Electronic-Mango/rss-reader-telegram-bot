"""
Module handling the "remove" command, allowing users to remove a single subscription.
"""

from collections import namedtuple
from logging import getLogger
from typing import Any, Callable

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler

from bot.user_filter import USER_FILTER
from db.wrapper import chat_has_stored_feeds, get_stored_feed_type_and_name, remove_stored_feed

REMOVE_HELP_MESSAGE = "/remove - remove subscription for a given feed"

_CONFIRM_STATE, _LIST_FEEDS_AGAIN_STATE = range(2)
_CONFIRM_REMOVAL_YES = "Yes"
_CONFIRM_REMOVAL_NO = "No"
_GO_BACK = "« Back to subscriptions"

_RemoveFeedData = namedtuple("_RemoveFeedData", ["feed_type", "feed_name"])
_logger = getLogger(__name__)


def remove_initial_handler() -> CommandHandler:
    return CommandHandler("remove", _handle_remove_request, USER_FILTER)


def remove_followup_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(_request_confirmation, _valid_data)],
        states={
            _CONFIRM_STATE: [
                CallbackQueryHandler(_remove_subscription, _valid_data),
                CallbackQueryHandler(_handle_go_back_to_subscription_list, f"^{_GO_BACK}$"),
                CallbackQueryHandler(_cancel, f"^{_CONFIRM_REMOVAL_NO}$"),
            ],
            _LIST_FEEDS_AGAIN_STATE: [CallbackQueryHandler(_request_confirmation, _valid_data)],
        },
        fallbacks=[CallbackQueryHandler(_cancel)],
        per_message=True,
        name="remove_followup_handler",
        persistent=True,
    )


def _valid_data(data: Any) -> bool:
    return isinstance(data, _RemoveFeedData)


async def _handle_remove_request(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User requested removal of subscription")
    if chat_has_stored_feeds(chat_id):
        await _request_feed_to_remove(update.message.reply_text, chat_id)
    else:
        await _no_feeds_to_remove(update.message, chat_id)


async def _handle_go_back_to_subscription_list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    _logger.info(f"[{chat_id}] User went back to subscriptions list")
    await _request_feed_to_remove(query.edit_message_text, chat_id)
    return _LIST_FEEDS_AGAIN_STATE


async def _request_feed_to_remove(response_callback: Callable, chat_id: int) -> None:
    keyboard = [
        [_prepare_feed_button(name, type)] for type, name in get_stored_feed_type_and_name(chat_id)
    ]
    await response_callback(
        "Select subscription to remove",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _no_feeds_to_remove(message: Message, chat_id: int) -> int:
    _logger.info(f"[{chat_id}] No subscriptions to remove")
    await message.reply_text("No subscriptions to remove")


async def _request_confirmation(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    feed_name, feed_type = query.data
    _logger.info(f"[{update.effective_chat.id}] Selected [{feed_name}] [{feed_type}] for removal")
    keyboard = [
        [
            InlineKeyboardButton(_CONFIRM_REMOVAL_YES, callback_data=query.data),
            InlineKeyboardButton(_CONFIRM_REMOVAL_NO, callback_data=_CONFIRM_REMOVAL_NO),
        ],
        [InlineKeyboardButton(_GO_BACK, callback_data=_GO_BACK)],
    ]
    await query.edit_message_text(
        f"Confirm removal of <b>{feed_name}</b> ({feed_type})",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return _CONFIRM_STATE


async def _remove_subscription(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    feed_name, feed_type = query.data
    _logger.info(f"[{chat_id}] Confirmed [{feed_name}] [{feed_type}] for removal")
    remove_stored_feed(chat_id, feed_type, feed_name)
    await query.edit_message_text(f"Removed subscription for <b>{feed_name}</b>!")
    return ConversationHandler.END


def _prepare_feed_button(name: str, type: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(f"{name} ({type})", callback_data=_RemoveFeedData(name, type))


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled removing subscription")
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("No subscriptions have beed removed")
    return ConversationHandler.END
