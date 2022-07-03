from logging import DEBUG, ERROR, INFO, WARN, basicConfig, debug, error, info, warn
from os import getenv

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, JobQueue

from basic_json_feed_reader import get_json_feed_items, get_not_handled_feed_items
from feed_item_sender_basic import send_message
from feed_item_sender_instagram import send_message_instagram
from rss_db import add_rss_to_db, get_all_rss_from_db, get_rss_from_db, remove_rss_feed_id_db, update_rss_feed_in_db


def main():
    load_dotenv()
    configure_logging()
    info("Bot starting...")
    application = ApplicationBuilder().token(getenv("TOKEN")).build()
    info("Bot started, setting handlers...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hello", hello))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("remove", remove))
    info("Handlers configured, starting RSS checking...")
    start_rss_checking_when_necessary(application.job_queue)
    info("RSS checking triggered, starting polling...")
    application.run_polling()


def configure_logging():
    basicConfig(format="%(asctime)s %(message)s", datefmt="%d-%m-%Y %H:%M:%S", level=INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Start from chat ID: [{update.effective_chat.id}]")
    await update.message.reply_text("Simple Web Comics bot based on RSS feeds!");


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Hello from chat ID: [{update.effective_chat.id}]")
    await update.message.reply_text("Hello there!");


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Add from chat ID: [{update.effective_chat.id}], with arguments: [{context.args}]")
    if len(context.args) != 2:
        await update.message.reply_text("Incorrect number of arguments! Pass RSS feed link and RSS feed name.")
        return
    rss_feed, rss_name = context.args
    chat_id = update.effective_chat.id
    feed_items = get_json_feed_items(rss_feed)
    latest_item_id = feed_items[0]["id"]
    info(f"Adding RSS feed, chat_id=[{chat_id}] name=[{rss_name}] feed=[{rss_feed}] latest=[{latest_item_id}]...")
    add_rss_to_db(chat_id, rss_feed, rss_name, latest_item_id)
    start_rss_checking_when_necessary(context.job_queue)
    await update.message.reply_text(f'Added subscription for "{rss_name}"!')


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    info(f"Remove from chat ID: [{update.effective_chat.id}], with arguments: [{context.args}]")
    if len(context.args) != 1:
        await update.message.reply_text("Incorrect number of arguments! Pass RSS feed name.")
        return
    rss_name = context.args[0]
    chat_id = update.effective_chat.id
    removed_count = remove_rss_feed_id_db(chat_id, rss_name)
    if removed_count:
        info(f"RSS chat_id=[{chat_id}] name=[{rss_name}] was removed.")
        await update.message.reply_text(f'Removed subscription for "{rss_name}"!')
    else:
        info(f"Removed no entries for chat_id=[{chat_id}] name=[{rss_name}], most likely this RSS name doesn't exist.")
        await update.message.reply_text(f'No subscription with name "{rss_name}" to remove!')


def start_rss_checking_when_necessary(job_queue: JobQueue):
    interval = int(getenv("LOOKUP_INTERVAL_SECONDS"))
    data_to_look_up = {chat_id: data for chat_id, data in get_all_rss_from_db().items() if data}
    for chat_id, data in data_to_look_up.items():
        if not data:
            info(f"No RSS feeds to check for chat ID=[{chat_id}].")
            continue
        job_name = f"check-rss-{chat_id}"
        if len(job_queue.get_jobs_by_name(job_name)) != 0:
            info(f"RSS checking job=[{job_name}] is already started.")
            continue
        info(f"Starting repeating job checking RSS for updates with interval=[{interval}] in chat ID=[{job_name}]")
        job_queue.run_repeating(check_rss, interval, name=job_name, chat_id=chat_id)


async def check_rss(context: ContextTypes.DEFAULT_TYPE):
    info(f"Checking all RSS...")
    chat_id = context.job.chat_id
    rss_feeds_to_check = get_rss_from_db(chat_id)
    not_handled_rss = prepare_all_not_handled_data(rss_feeds_to_check)
    if not not_handled_rss:
        info("No updates.")
        return
    info("Found new RSS items.")
    info(not_handled_rss)
    for rss_name, rss_feed, items in not_handled_rss:
        for item in items:
            await send_rss_update(context, chat_id, rss_name, item)
        latest_item = items[-1]
        update_rss_feed_in_db(chat_id, rss_feed, rss_name, latest_item["id"])


def prepare_all_not_handled_data(stored_rss_data):
    not_handled_rss_data = [
        get_not_handled_rss_data_for_channel(rss_data)
        for rss_data in stored_rss_data
    ]
    return [
        not_handled_rss_data
        for not_handled_rss_data in not_handled_rss_data
        if not_handled_rss_data
    ]


def get_not_handled_rss_data_for_channel(rss_data):
    rss_name = rss_data["rss_name"]
    rss_feed = rss_data["rss_feed"]
    latest_handled_item_id = rss_data["latest_item_id"]
    not_handled_feed_items = get_not_handled_feed_items(rss_feed, latest_handled_item_id)
    if not not_handled_feed_items:
        return ()
    return (rss_name, rss_feed, not_handled_feed_items)


async def send_rss_update(context: ContextTypes.DEFAULT_TYPE, chat_id, rss_name, item):
    info(f"Sending message to ID=[{chat_id}]")
    item_id = item["id"]
    if "www.instagram.com" in item_id:
        await send_message_instagram(context, chat_id, rss_name, item)
    else:
        await send_message(context, chat_id, rss_name, item)


if __name__ == '__main__':
    main()
