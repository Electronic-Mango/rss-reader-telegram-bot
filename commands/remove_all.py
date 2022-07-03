from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import get_rss_data_for_chat, remove_chat_collection
from rss_checking import cancel_checking_job

REMOVE_ALL_HELP_MESSAGE = "/remove_all - remove all subscriptions"


def remove_all_command_handler():
    return CommandHandler("remove_all", remove_all)


async def remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    info(f"Remove all from chat ID: [{chat_id}]")
    for feed_data in get_rss_data_for_chat(chat_id):
        cancel_checking_job(context, chat_id, feed_data.feed_name)
    remove_chat_collection(chat_id)
    await update.message.reply_text("Removed all subscriptions")
