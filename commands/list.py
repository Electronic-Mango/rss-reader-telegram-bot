from logging import getLogger

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import get_rss_data_for_chat

LIST_HELP_MESSAGE = "/list - list all subscriptions"

_logger = getLogger(__name__)


def list_command_handler():
    return CommandHandler("list", _list)


async def _list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    _logger.info(f"List from chat ID: [{chat_id}]")
    rss_data = get_rss_data_for_chat(chat_id)
    if not rss_data:
        await update.message.reply_text("No feeds subscribed.")
        return
    formatted_rss_data = [_format_feed_item(rss_data) for rss_data in rss_data]
    message = "Following feeds are subscribed:\n\n"
    message += "\n".join(sorted(formatted_rss_data))
    await update.message.reply_text(message, parse_mode="HTML")


def _format_feed_item(rss_feed_data):
    feed_name, feed_type, _, _ = rss_feed_data
    return f"<b>{feed_name}</b> - {feed_type}"
