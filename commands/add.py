# TODO Consider allowing for adding feeds via single command as well

from logging import getLogger
from os import getenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, MessageHandler
from telegram.ext.filters import TEXT, COMMAND

from feed_reader import feed_exists, get_latest_feed_entry_id
from feed_types import feed_type_to_rss
from rss_checking import start_rss_checking
from db import add_rss_to_db, feed_is_in_db

ADD_HELP_MESSAGE = "/add - adds subscription for a given feed"

_FEED_TYPES_PER_KEYBOARD_ROW = 2
_FEED_TYPE, _FEED_NAME = range(2)

_logger = getLogger(__name__)


def add_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("add", _request_feed_type)],
        states={
            _FEED_TYPE: [MessageHandler(TEXT & ~COMMAND, _handle_feed_type)],
            _FEED_NAME: [MessageHandler(TEXT & ~COMMAND, _store_subscription)],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
    )


async def _cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _logger.info(f"User cancelled adding subscription chat ID=[{update.effective_chat.id}].")
    await update.message.reply_text(
        "Cancelled adding subscription", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def _request_feed_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _logger.info("User requested new subscription.")
    all_feed_types = list(feed_type_to_rss().keys())
    keyboard = [
        all_feed_types[x : x + _FEED_TYPES_PER_KEYBOARD_ROW]
        for x in range(0, len(all_feed_types), _FEED_TYPES_PER_KEYBOARD_ROW)
    ]
    await update.message.reply_text(
        "Select source, or /cancel",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            input_field_placeholder="Select feed type"
        )
    )
    return _FEED_TYPE


async def _handle_feed_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_type = update.message.text
    context.user_data[_FEED_TYPE] = feed_type
    _logger.info(f"User selected type=[{feed_type}].")
    return await _request_feed_name(update, feed_type)


async def _store_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_name = update.message.text
    _logger.info(f"User send feed name: {feed_name}.")
    chat_id = update.effective_chat.id
    feed_type = context.user_data[_FEED_TYPE]
    if feed_is_in_db(chat_id, feed_type, feed_name):
        return await _feed_with_given_name_already_exists(update, feed_name, feed_type)
    feed_link = _get_feed_link(feed_name, feed_type)
    if not feed_exists(feed_link):
        return await _feed_does_not_exist(update, feed_type, feed_name)
    latest_entry_id = get_latest_feed_entry_id(feed_link)
    _logger.info(
        f"Adding RSS feed"
        f"chat_id=[{chat_id}] "
        f"name=[{feed_name}] "
        f"type=[{feed_type}] "
        f"feed=[{feed_link}] "
        f"latest=[{latest_entry_id}]..."
    )
    rss_data = add_rss_to_db(chat_id, feed_name, feed_type, feed_link, latest_entry_id)
    start_rss_checking(context.job_queue, chat_id, rss_data)
    await update.message.reply_text(f"Added subscription for <b>{feed_name}</b>!", parse_mode="HTML")
    return ConversationHandler.END


def _get_feed_link(feed_name, feed_type):
    instagram_feed_link = feed_type_to_rss()[feed_type]
    user_pattern = getenv("RSS_FEED_USER_PATTERN")
    return instagram_feed_link.replace(user_pattern, feed_name)


async def _feed_with_given_name_already_exists(update, feed_name, feed_type):
    await update.message.reply_text(
        f"Subscription with name <b>{feed_name}</b> ({feed_type}) already exists!",
        parse_mode="HTML",
    )
    return await _request_feed_name(update, feed_type)


async def _feed_does_not_exist(update, feed_type, feed_name):
    await update.message.reply_text(
        f"Feed for user <b>{feed_name}</b> doesn't exist!",
        parse_mode="HTML",
    )
    return await _request_feed_name(update, feed_type)


async def _request_feed_name(update, feed_type):
    await update.message.reply_text(f"Send {feed_type} user, or /cancel")
    return _FEED_NAME
