"""
Module handling the "add" command, allowing users to add new RSS subscriptions.
"""

from enum import Enum, auto
from typing import NamedTuple

from feedparser import FeedParserDict
from loguru import logger
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
from feed.reader import feed_is_valid, get_latest_data, get_parsed_feed
from settings import RSS_FEEDS

ADD_HELP_MESSAGE = "/add - adds subscription for a given feed"


class _ConversationState(Enum):
    FEED_NAME = auto()


class _AddFeedData(NamedTuple):
    feed_type: str


def add_initial_handler() -> CommandHandler:
    return CommandHandler("add", _request_feed_type, USER_FILTER)


def add_followup_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(_request_feed_names, _AddFeedData)],
        states={
            _ConversationState.FEED_NAME: [
                MessageHandler(USER_FILTER & TEXT & ~COMMAND, _handle_feed_names),
                CommandHandler("cancel", _cancel, USER_FILTER),
            ],
        },
        fallbacks=[CommandHandler("cancel", _cancel, USER_FILTER)],
        allow_reentry=True,
        name="add_followup_handler",
        persistent=True,
    )


async def _request_feed_type(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"[{update.effective_chat.id}] User requested new subscription")
    keyboard = [
        [InlineKeyboardButton(name, callback_data=_AddFeedData(name))] for name in RSS_FEEDS.keys()
    ]
    await update.message.reply_text(
        "Select source:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def _request_feed_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    feed_type = query.data.feed_type
    context.user_data[_ConversationState.FEED_NAME] = feed_type
    logger.info(f"[{update.effective_chat.id}] User selected type [{feed_type}], requesting name")
    await update.effective_chat.send_message(
        f"Send <b>{feed_type}</b> name, multiple names separated by a space, or /cancel",
    )
    return _ConversationState.FEED_NAME


async def _handle_feed_names(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    feed_names = update.message.text.split()
    feed_type = context.user_data[_ConversationState.FEED_NAME]
    logger.info(f"{chat_id} User send feed name {feed_names} for [{feed_type}]")
    for feed_name in feed_names:
        await _handle_feed_name(update.message, chat_id, feed_type, feed_name)
    return ConversationHandler.END


async def _handle_feed_name(message: Message, chat_id: int, feed_type: str, feed_name: str) -> None:
    if feed_is_already_stored(chat_id, feed_type, feed_name):
        await _feed_with_given_name_already_exists(message, chat_id, feed_name, feed_type)
    elif feed_is_valid(parsed_feed := get_parsed_feed(feed_type, feed_name)):
        await _store_subscription(message, chat_id, parsed_feed, feed_type, feed_name)
    else:
        await _feed_does_not_exist(message, chat_id, feed_type, feed_name)


async def _feed_with_given_name_already_exists(
    message: Message,
    chat_id: int,
    feed_name: str,
    feed_type: str,
) -> None:
    logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] is subscribed")
    await message.reply_text(f"Subscription for <b>{feed_name}</b> ({feed_type}) already exists!")


async def _store_subscription(
    message: Message,
    chat_id: int,
    parsed_feed: FeedParserDict,
    feed_type: str,
    feed_name: str,
) -> None:
    id, link, date = get_latest_data(parsed_feed)
    store_feed_data(chat_id, feed_name, feed_type, id, link, date)
    await message.reply_text(f"Added subscription for <b>{feed_name}</b>!")


async def _feed_does_not_exist(
    message: Message,
    chat_id: int,
    feed_type: str,
    feed_name: str,
) -> None:
    logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] doesn't exist")
    await message.reply_text(f"Feed for source <b>{feed_name}</b> doesn't exist!")


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"[{update.effective_chat.id}] User cancelled adding subscription")
    await update.message.reply_text("Cancelled adding subscription")
    return ConversationHandler.END
