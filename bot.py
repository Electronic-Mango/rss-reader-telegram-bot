from logging import DEBUG, ERROR, INFO, WARN, basicConfig, debug, error, info, warn
from os import getenv

from dotenv import load_dotenv
from telegram.ext import JobQueue
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.updater import Updater
from telegram.update import Update

from basic_json_feed_reader import get_json_feed_items, get_not_handled_feed_items
from feed_item_sender_basic import send_message
from feed_item_sender_instagram import send_message_instagram
from rss_db import add_rss_to_db, get_all_rss_from_db, remove_rss_feed_id_db, update_rss_feed_in_db


def main():
    load_dotenv()
    configure_logging()
    info("Bot starting...")
    updater = Updater(getenv("TOKEN"), use_context=True)
    info("Bot started, setting handlers...")
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("hello", hello))
    updater.dispatcher.add_handler(CommandHandler("add", add))
    updater.dispatcher.add_handler(CommandHandler("remove", remove))
    info("Handlers configured, starting RSS checking...")
    start_rss_checking_when_necessary(updater.job_queue)
    info("RSS checking triggered, starting polling...")
    updater.start_polling()
    updater.idle()


def configure_logging():
    basicConfig(format="%(asctime)s %(message)s", datefmt="%d-%m-%Y %H:%M:%S", level=INFO)


def start(update: Update, context: CallbackContext):
    info(f"Start from chat ID: [{update.message.chat_id}]")
    update.message.reply_text("Simple Web Comics bot based on RSS feeds!");


def hello(update: Update, context: CallbackContext):
    info(f"Hello from chat ID: [{update.message.chat_id}]")
    update.message.reply_text("Hello there!");


def add(update: Update, context: CallbackContext):
    info(f"Add from chat ID: [{update.message.chat_id}], with arguments: [{context.args}]")
    if len(context.args) != 2:
        update.message.reply_text("Incorrect number of arguments! Pass RSS feed link and RSS feed name.")
        return
    rss_feed, rss_name = context.args
    chat_id = update.message.chat_id
    feed_items = get_json_feed_items(rss_feed)
    latest_item_id = feed_items[0]["id"]
    info(f"Adding RSS feed, chat_id=[{chat_id}] name=[{rss_name}] feed=[{rss_feed}] latest=[{latest_item_id}]...")
    add_rss_to_db(chat_id, rss_feed, rss_name, latest_item_id)
    start_rss_checking_when_necessary(context.job_queue)
    update.message.reply_text(f'Added subscription for "{rss_name}"!')


def remove(update: Update, context: CallbackContext):
    info(f"Remove from chat ID: [{update.message.chat_id}], with arguments: [{context.args}]")
    if len(context.args) != 1:
        update.message.reply_text("Incorrect number of arguments! Pass RSS feed name.")
        return
    rss_name = context.args[0]
    chat_id = update.message.chat_id
    removed_count = remove_rss_feed_id_db(chat_id, rss_name)
    if removed_count:
        info(f"RSS chat_id=[{chat_id}] name=[{rss_name}] was removed.")
        update.message.reply_text(f'Removed subscription for "{rss_name}"!')
    else:
        info(f"Removed no entries for chat_id=[{chat_id}] name=[{rss_name}], most likely this RSS name doesn't exist.")
        update.message.reply_text(f'No subscription with name "{rss_name}" to remove!')


def start_rss_checking_when_necessary(job_queue: JobQueue):
    if len(job_queue.get_jobs_by_name("check-rss")) != 0:
        info("RSS checking job is already started.")
        return
    data_to_look_up = {collection: data for collection, data in get_all_rss_from_db().items() if data}
    if data_to_look_up:
        interval = getenv("LOOKUP_INTERVAL_SECONDS")
        info(f"Starting repeating job checking RSS for updates with interval=[{interval}]")
        job_queue.run_repeating(check_rss, interval, name="check-rss")
    else:
        info("No RSS feeds to check, job is not started.")


def check_rss(context: CallbackContext):
    info(f"Checking all RSS...")
    not_handled_rss = prepare_all_not_handled_data(get_all_rss_from_db())
    if not not_handled_rss:
        info("No updates.")
        return
    info("Found new RSS items.")
    info(not_handled_rss)
    for chat_id, rss_channel_data in not_handled_rss.items():
        for rss_name, rss_feed, items in rss_channel_data:
            for item in items:
                send_rss_update(context, chat_id, rss_name, item)
            latest_item = items[-1]
            update_rss_feed_in_db(chat_id, rss_feed, rss_name, latest_item["id"])


def prepare_all_not_handled_data(stored_rss_data):
    not_handled_rss_data = {
        int(channel_id): get_not_handled_rss_data_for_channel(rss_data)
        for channel_id, rss_data in stored_rss_data.items()
    }
    return {
        channel_id: not_handled_rss_data
        for channel_id, not_handled_rss_data in not_handled_rss_data.items()
        if not_handled_rss_data
    }


def get_not_handled_rss_data_for_channel(all_rss_data):
    not_handled_items = list()
    for rss_data in all_rss_data:
        rss_name = rss_data["rss_name"]
        rss_feed = rss_data["rss_feed"]
        latest_handled_item_id = rss_data["latest_item_id"]
        not_handled_feed_items = get_not_handled_feed_items(rss_feed, latest_handled_item_id)
        if not_handled_feed_items:
            not_handled_items.append((rss_name, rss_feed, not_handled_feed_items))
    return not_handled_items


def send_rss_update(context: CallbackContext, chat_id, rss_name, item):
    info(f"Sending message to ID=[{chat_id}]")
    item_id = item["id"]
    if "www.instagram.com" in item_id:
        send_message_instagram(context, chat_id, rss_name, item)
    else:
        send_message(context, chat_id, rss_name, item)


if __name__ == '__main__':
    main()
