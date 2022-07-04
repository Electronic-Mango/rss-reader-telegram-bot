# TODO Consider allowing for adding feeds via single command as well

from logging import getLogger
from os import getenv
from dotenv import load_dotenv

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, MessageHandler
from telegram.ext.filters import TEXT, COMMAND

from feed_types import FeedTypes
from instagram_feed_reader import feed_exists, get_json_feed_items
from rss_checking import start_rss_checking
from db import add_rss_to_db, feed_is_in_db

ADD_HELP_MESSAGE = "/add - adds subscription for a given feed"

_FEED_TYPE, _FEED_LINK, _FEED_NAME = range(3)

_logger = getLogger(__name__)


def add_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("add", request_feed_type)],
        states={
            _FEED_TYPE: [MessageHandler(TEXT & ~COMMAND, handle_feed_type)],
            _FEED_LINK: [MessageHandler(TEXT & ~COMMAND, request_feed_name)],
            _FEED_NAME: [MessageHandler(TEXT & ~COMMAND, store_subscription)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _logger.info(f"User cancelled adding subscription chat ID=[{update.effective_chat.id}].")
    await update.message.reply_text(
        "Cancelled adding subscription", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def request_feed_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _logger.info("User requested new subscription.")
    keyboard = [[FeedTypes.INSTAGRAM_TYPE, FeedTypes.RAW_RSS_TYPE]]
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


async def handle_feed_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_type = update.message.text
    context.user_data[_FEED_TYPE] = feed_type
    _logger.info(f"User selected type=[{feed_type}].")
    match feed_type:
        case FeedTypes.INSTAGRAM_TYPE:
            await update.message.reply_text("Send Instagram user, or /cancel")
            return _FEED_NAME
        case FeedTypes.RAW_RSS_TYPE:
            await update.message.reply_text("Send RSS feed link, or /cancel")
            return _FEED_LINK
        case _:
            await update.message.reply_text("Incorrect RSS feed type!")
            return await request_feed_type(update, context)


async def request_feed_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_link = update.message.text
    _logger.info(f"User send feed link: {feed_link}.")
    context.user_data[_FEED_LINK] = feed_link
    await update.message.reply_text("Send RSS feed name, or /cancel")
    return _FEED_NAME


async def store_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_name = update.message.text
    _logger.info(f"User send feed name: {feed_name}.")
    chat_id = update.effective_chat.id
    feed_type = context.user_data[_FEED_TYPE]
    if feed_is_in_db(chat_id, feed_type, feed_name):
        return await feed_with_given_name_already_exists(context, update, feed_name, feed_type)
    feed_link = get_feed_link(context, feed_name, feed_type)
    if not feed_exists(feed_link):
        return await feed_does_not_exist(context, update, feed_name)
    feed_items = get_json_feed_items(feed_link)
    latest_item_id = feed_items[0]["id"]
    _logger.info(
        f"Adding RSS feed"
        f"chat_id=[{chat_id}] "
        f"name=[{feed_name}] "
        f"type=[{feed_type}] "
        f"feed=[{feed_link}] "
        f"latest=[{latest_item_id}]..."
    )
    rss_data = add_rss_to_db(chat_id, feed_name, feed_type, feed_link, latest_item_id)
    start_rss_checking(context.job_queue, chat_id, rss_data)
    await update.message.reply_text(f"Added subscription for <b>{feed_name}</b>!", parse_mode="HTML")
    return ConversationHandler.END


# TODO Move this to the feed type dispatcher?
def get_feed_link(context, feed_name, feed_type):
    if feed_type == FeedTypes.INSTAGRAM_TYPE:
        load_dotenv()
        instagram_feed_link = getenv("INSTAGRAM_RSS_FEED_LINK")
        user_pattern = getenv("INSTAGRAM_RSS_FEED_USER_PATTERN")
        return instagram_feed_link.replace(user_pattern, feed_name)
    else:
        return context.user_data[_FEED_LINK]


async def feed_with_given_name_already_exists(context, update, feed_name, feed_type):
    await update.message.reply_text(
        f"Subscription with name <b>{feed_name}</b> ({feed_type}) already exists!",
        parse_mode="HTML",
    )
    return await request_feed_name(update, context)


async def feed_does_not_exist(context, update, feed_name):
    await update.message.reply_text(
        f"Feed for user <b>{feed_name}</b> doesn't exist!",
        parse_mode="HTML",
    )
    return await request_feed_name(update, context)
