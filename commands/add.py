from logging import getLogger

from telegram import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, JobQueue, MessageHandler
from telegram.ext.filters import TEXT, COMMAND

from db import add_feed_to_db, feed_is_in_db
from feed_reader import feed_exists, get_latest_id
from settings import RSS_FEEDS

ADD_HELP_MESSAGE = "/add - adds subscription for a given feed"

# TODO Extract to .env file?
_FEED_TYPES_PER_KEYBOARD_ROW = 2
_FEED_TYPE, _FEED_NAME = range(2)

_logger = getLogger(__name__)


def add_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("add", _request_feed_type)],
        states={
            _FEED_TYPE: [MessageHandler(TEXT & ~COMMAND, _handle_feed_type)],
            _FEED_NAME: [MessageHandler(TEXT & ~COMMAND, _handle_feed_names)],
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
    _logger.info(f"[{update.effective_chat.id}] User selected type [{feed_type}], requesting name")
    await update.message.reply_text(
        f"Send <b>{feed_type}</b> source, you can send multiple separated by a space, or /cancel",
        parse_mode="HTML",
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
    if feed_is_in_db(chat_id, feed_type, feed_name):
        await _feed_with_given_name_already_exists(message, chat_id, feed_name, feed_type)
    elif not feed_exists(feed_type, feed_name):
        await _feed_does_not_exist(message, chat_id, feed_type, feed_name)
    else:
        await _store_subscription(message, chat_id, feed_type, feed_name)


async def _feed_with_given_name_already_exists(
    message: Message,
    chat_id: int,
    feed_name: str,
    feed_type: str
) -> None:
    _logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] is subscribed")
    await message.reply_text(
        f"Subscription with name <b>{feed_name}</b> ({feed_type}) already exists!",
        parse_mode="HTML",
    )


async def _feed_does_not_exist(
    message: Message,
    chat_id: int,
    feed_type: str,
    feed_name: str
) -> None:
    _logger.info(f"{chat_id} Feed [{feed_name}][{feed_type}] doesn't exist")
    await message.reply_text(
        f"Feed for source <b>{feed_name}</b> doesn't exist!",
        parse_mode="HTML",
    )


async def _store_subscription(
    message: Message,
    chat_id: int,
    feed_type: str,
    feed_name: str
) -> None:
    latest_id = get_latest_id(feed_type, feed_name)
    add_feed_to_db(chat_id, feed_name, feed_type, latest_id)
    await message.reply_text(
        f"Added subscription for <b>{feed_name}</b>!",
        parse_mode="HTML"
    )
