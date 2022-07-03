from logging import info

from telegram import Update
from telegram.ext import CommandHandler, ConversationHandler, ContextTypes, MessageHandler
from telegram.ext.filters import TEXT, COMMAND

from basic_json_feed_reader import get_json_feed_items
from rss_checking import start_rss_checking
from rss_db import add_rss_to_db, get_rss_feed

ADD_HELP_MESSAGE = "/add - adds subscription for a given feed"
ADD_LINK, ADD_NAME = range(2)


def add_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("add", request_feed_link)],
        states={
            ADD_LINK: [MessageHandler(TEXT & ~COMMAND, request_feed_name)],
            ADD_NAME: [MessageHandler(TEXT & ~COMMAND, store_subscription)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"User cancelled adding subscription chat ID=[{update.effective_chat.id}].")
    await update.message.reply_text("Cancelled adding subscription.")
    return ConversationHandler.END


async def request_feed_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info("User requested new subscription.")
    await update.message.reply_text("Send RSS feed link, or /cancel.")
    return ADD_LINK


async def request_feed_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_link = update.message.text
    info(f"User send feed link: {feed_link}.")
    context.user_data[ADD_LINK] = feed_link
    await update.message.reply_text("Send RSS feed name, or /cancel.")
    return ADD_NAME


async def store_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feed_name = update.message.text
    info(f"User send feed name: {feed_name}.")
    chat_id = update.effective_chat.id
    existing_feed = get_rss_feed(chat_id, feed_name)
    if existing_feed is not None:
        await update.message.reply_text(
            f"Subscription for <b>{feed_name}</b> already exists!"
            f"\nFeed: <code>{existing_feed.rss_feed}</code>"
            f"\n\nType in a different name or /cancel.",
            parse_mode="HTML",
        )
        return ADD_NAME
    feed_link = context.user_data[ADD_LINK]
    feed_items = get_json_feed_items(feed_link)
    latest_item_id = feed_items[0]["id"]
    info(
        f"Adding RSS feed"
        f"chat_id=[{chat_id}] "
        f"name=[{feed_name}] "
        f"feed=[{feed_link}] "
        f"latest=[{latest_item_id}]..."
    )
    rss_data = add_rss_to_db(chat_id, feed_link, feed_name, latest_item_id)
    start_rss_checking(context.job_queue, chat_id, rss_data)
    await update.message.reply_text(f"Added subscription for <b>{feed_name}</b>!", parse_mode="HTML")
    return ConversationHandler.END
