# TODO Consider allowing for adding feeds via single command as well

from logging import getLogger

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, MessageHandler
from telegram.ext.filters import TEXT, COMMAND

from db import add_feed_to_db, feed_is_in_db
from feed_reader import feed_exists, get_latest_feed_entry_id
from rss_checking import start_rss_checking
from settings import RSS_FEEDS

ADD_HELP_MESSAGE = "/add - adds subscription for a given feed"

_FEED_TYPES_PER_KEYBOARD_ROW = 2
_FEED_TYPE, _FEED_NAME = range(2)

_logger = getLogger(__name__)


def add_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("add", _request_feed_type)],
        states={
            _FEED_TYPE: [MessageHandler(TEXT & ~COMMAND, _handle_feed_type)],
            _FEED_NAME: [MessageHandler(TEXT & ~COMMAND, _store_subscription)],
        },
        fallbacks=[CommandHandler("cancel", _cancel)],
    )


async def _cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User cancelled adding subscription")
    await update.message.reply_text(
        "Cancelled adding subscription", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def _request_feed_type(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    _logger.info(f"[{update.effective_chat.id}] User requested new subscription")
    all_feed_types = list(RSS_FEEDS.keys())
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
            input_field_placeholder="Select feed type",
        ),
    )
    return _FEED_TYPE


async def _handle_feed_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    feed_type = update.message.text
    context.user_data[_FEED_TYPE] = feed_type
    _logger.info(f"[{update.effective_chat.id}] User selected type [{feed_type}]")
    return await _request_feed_name(update, feed_type)


async def _store_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    feed_name = update.message.text
    chat_id = update.effective_chat.id
    _logger.info(f"{chat_id} User send feed name [{feed_name}]")
    feed_type = context.user_data[_FEED_TYPE]
    if feed_is_in_db(chat_id, feed_type, feed_name):
        return await _feed_with_given_name_already_exists(update, chat_id, feed_name, feed_type)
    feed_link = _get_feed_link(feed_name, feed_type)
    if not feed_exists(feed_link):
        return await _feed_does_not_exist(update, chat_id, feed_type, feed_name)
    latest_entry_id = get_latest_feed_entry_id(feed_link)
    rss_data = add_feed_to_db(chat_id, feed_name, feed_type, feed_link, latest_entry_id)
    start_rss_checking(context.job_queue, chat_id, rss_data)
    await update.message.reply_text(
        f"Added subscription for <b>{feed_name}</b>!", parse_mode="HTML"
    )
    return ConversationHandler.END


def _get_feed_link(feed_name: str, feed_type: str) -> str:
    return RSS_FEEDS[feed_type].format(source_pattern=feed_name)


async def _feed_with_given_name_already_exists(update, chat_id, feed_name, feed_type) -> int:
    _logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] is subscribed")
    await update.message.reply_text(
        f"Subscription with name <b>{feed_name}</b> ({feed_type}) already exists!",
        parse_mode="HTML",
    )
    return await _request_feed_name(update, feed_type)


async def _feed_does_not_exist(update, chat_id, feed_type, feed_name) -> int:
    _logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] doesn't exist")
    await update.message.reply_text(
        f"Feed for source <b>{feed_name}</b> doesn't exist!",
        parse_mode="HTML",
    )
    return await _request_feed_name(update, feed_type)


async def _request_feed_name(update, feed_type) -> int:
    _logger.info(f"[{update.effective_chat.id}] Requesting feed name")
    await update.message.reply_text(f"Send {feed_type} source, or /cancel")
    return _FEED_NAME
