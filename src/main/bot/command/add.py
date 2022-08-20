"""
Module handling the "add" command, allowing users to add new RSS subscriptions.
"""

from logging import getLogger

from feedparser import FeedParserDict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
)
from telegram.ext.filters import COMMAND, TEXT

from bot.user_filter import USER_FILTER
from db.wrapper import feed_is_already_stored, store_feed_data
from feed.reader import feed_is_valid, get_latest_id, get_parsed_feed
from settings import RSS_FEEDS

ADD_HELP_MESSAGE = "/add - adds subscription for a given feed"

_FEED_TYPE, _FEED_NAME = range(2)

_logger = getLogger(__name__)


def add_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("add", _request_feed_type, USER_FILTER)],
        states={
            _FEED_TYPE: [CallbackQueryHandler(_handle_feed_type)],
            _FEED_NAME: [MessageHandler(USER_FILTER & TEXT & ~COMMAND, _handle_feed_names)],
        },
        fallbacks=[CommandHandler("cancel", _cancel, USER_FILTER)],
    )


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled adding subscription")
    await update.message.reply_text("Cancelled adding subscription")
    return ConversationHandler.END


async def _request_feed_type(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User requested new subscription")
    await update.message.reply_text(
        "Select source for new subscription",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(name, callback_data=name)] for name in RSS_FEEDS.keys()]
        ),
    )
    return _FEED_TYPE


async def _handle_feed_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    feed_type = query.data
    context.user_data[_FEED_TYPE] = feed_type
    _logger.info(f"[{update.effective_chat.id}] User selected type [{feed_type}], requesting name")
    await query.edit_message_text(
        f"Send <b>{feed_type}</b> source, you can send multiple separated by a space, or /cancel"
    )
    return _FEED_NAME


async def _handle_feed_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    feed_names = update.message.text.split()
    feed_type = context.user_data[_FEED_TYPE]
    _logger.info(f"{chat_id} User send feed name {feed_names} for [{feed_type}]")
    for feed_name in feed_names:
        await _handle_feed_name(update.message, chat_id, feed_type, feed_name)
    return ConversationHandler.END


async def _handle_feed_name(message: Message, chat_id: int, feed_type: str, feed_name: str) -> None:
    if feed_is_already_stored(chat_id, feed_type, feed_name):
        await _feed_with_given_name_already_exists(message, chat_id, feed_name, feed_type)
        return
    parsed_feed = get_parsed_feed(feed_type, feed_name)
    if feed_is_valid(parsed_feed):
        await _store_subscription(message, chat_id, parsed_feed, feed_type, feed_name)
    else:
        await _feed_does_not_exist(message, chat_id, feed_type, feed_name)


async def _feed_with_given_name_already_exists(
    message: Message,
    chat_id: int,
    feed_name: str,
    feed_type: str,
) -> None:
    _logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] is subscribed")
    await message.reply_text(f"Subscription for <b>{feed_name}</b> ({feed_type}) already exists!")


async def _feed_does_not_exist(
    message: Message,
    chat_id: int,
    feed_type: str,
    feed_name: str,
) -> None:
    _logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] doesn't exist")
    await message.reply_text(f"Feed for source <b>{feed_name}</b> doesn't exist!")


async def _store_subscription(
    message: Message,
    chat_id: int,
    parsed_feed: FeedParserDict,
    feed_type: str,
    feed_name: str,
) -> None:
    latest_id = get_latest_id(parsed_feed)
    store_feed_data(chat_id, feed_name, feed_type, latest_id)
    await message.reply_text(f"Added subscription for <b>{feed_name}</b>!")
