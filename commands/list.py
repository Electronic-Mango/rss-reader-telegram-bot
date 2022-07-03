from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import get_rss_data_for_chat
from feed_types import FeedTypes

LIST_HELP_MESSAGE = "/list - list all subscriptions"


def list_command_handler():
    return CommandHandler("list", list)


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    info(f"List from chat ID: [{chat_id}]")
    rss_data = get_rss_data_for_chat(chat_id)
    if not rss_data:
        await update.message.reply_text("No feeds subscribed.")
        return
    formatted_rss_data = [format_feed_item(rss_data) for rss_data in rss_data]
    message = "Following feeds are subscribed:\n"
    message += "\n".join(formatted_rss_data)
    await update.message.reply_text(message, parse_mode="HTML")


def format_feed_item(rss_feed_data):
    feed_name, feed_type, feed_link, _ = rss_feed_data
    feed_item_str = f"<b>{feed_name}</b> - "
    if feed_type == FeedTypes.INSTAGRAM_TYPE:
        return feed_item_str + feed_type
    else:
        return feed_item_str + feed_type + f" (<code>{feed_link}</code>)"
