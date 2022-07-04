# TODO Allow removing feed via a single command, rather than a conversation

from logging import getLogger
from re import match

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, MessageHandler
from telegram.ext.filters import COMMAND, TEXT

from db import chat_has_feeds, get_rss_data_for_chat, remove_feed_link_id_db
from rss_checking import cancel_checking_job

REMOVE_HELP_MESSAGE = "/remove - remove subscription for a given feed"

_CONFIRM_REMOVAL_YES = "Yes"
_REMOVE_FEED, _CONFIRM = range(2)

_logger = getLogger(__name__)


def remove_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("remove", request_feed_name)],
        states={
            _REMOVE_FEED: [MessageHandler(TEXT & ~COMMAND, confirm_removal)],
            _CONFIRM: [MessageHandler(TEXT & ~COMMAND, remove_subscription)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _logger.info(f"User cancelled removing subscription chat ID=[{update.effective_chat.id}].")
    await update.message.reply_text(
        "Cancelled removing subscription", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def request_feed_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _logger.info(f"User requested cancellation of a subscription")
    if not chat_has_feeds(update.effective_chat.id):
        await update.message.reply_text("No subscriptions to remove")
        return ConversationHandler.END
    all_feed_names = [
        [_feed_data_to_keyboard_button(feed_data)]
        for feed_data in get_rss_data_for_chat(update.effective_chat.id)
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


async def confirm_removal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard_message = update.message.text
    feed_name, feed_type = _feed_name_and_type_from_keyboard_message(keyboard_message)
    _logger.info(f"User provided feed to remove [{feed_name} ({feed_type})]")
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


async def remove_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    confirmation = update.message.text
    if confirmation != _CONFIRM_REMOVAL_YES:
        return await cancel(update, context)
    feed_type, feed_name = context.user_data[_REMOVE_FEED]
    _logger.info(f"User confirmed removal of feed=[{feed_name} ({feed_type})]")
    chat_id = update.effective_chat.id
    remove_feed_link_id_db(chat_id, feed_type, feed_name)
    cancel_checking_job(context, chat_id, feed_type, feed_name)
    _logger.info(f"RSS chat_id=[{chat_id}] name=[{feed_name}] was removed.")
    await update.message.reply_text(
        f"Removed subscription for <b>{feed_name}</b>!", parse_mode="HTML"
    )
    return ConversationHandler.END


def _feed_data_to_keyboard_button(feed_data):
    return f"{feed_data.feed_name} ({feed_data.feed_type})"


def _feed_name_and_type_from_keyboard_message(keyboard_message: str):
    _logger.info(keyboard_message)
    keyboard_message_pattern = r"(.+)+ \((.+)\)"
    keyboard_message_match = match(keyboard_message_pattern, keyboard_message)
    return keyboard_message_match.groups()
