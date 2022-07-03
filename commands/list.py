from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from rss_db import get_rss_data_for_chat


def list_command_handler():
    return CommandHandler("list", list)


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    info(f"List from chat ID: [{chat_id}]")
    rss_data = get_rss_data_for_chat(chat_id)
    if not rss_data:
        await update.message.reply_text("No feeds subscribed.")
        return
    rss_data = [(rss_data.rss_name, rss_data.rss_feed) for rss_data in rss_data]
    rss_data = [
        f"<b>{rss_name}</b> - <code>{rss_feed}</code>"
        for rss_name, rss_feed in rss_data
    ]
    message = "Following feeds are subscribed:\n"
    message += "\n".join(rss_data)
    await update.message.reply_text(message, parse_mode="HTML")
