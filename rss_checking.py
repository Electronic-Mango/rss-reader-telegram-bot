from logging import info
from os import getenv

from telegram.ext import ContextTypes, JobQueue

from basic_json_feed_reader import get_not_handled_feed_items
from db import RssFeedData, update_rss_feed_in_db
from feed_item_sender_basic import send_message
from feed_item_sender_instagram import send_message_instagram


def rss_checking_job_name(chat_id: str, rss_name: str):
    return f"check-rss-{chat_id}-{rss_name}"


def start_rss_checking(job_queue: JobQueue, chat_id: str, rss_data: RssFeedData):
    info(str(rss_data))
    job_name = rss_checking_job_name(chat_id, rss_data.rss_name)
    if job_queue.get_jobs_by_name(job_name):
        info(f"RSS checking job=[{job_name}] is already started.")
        return
    interval = int(getenv("LOOKUP_INTERVAL_SECONDS"))
    info(
        f"Starting repeating job checking RSS for updates "
        f"with interval=[{interval}] "
        f"in chat ID=[{job_name}] "
        f"RSS=[{rss_data.rss_name}]"
    )
    job_queue.run_repeating(
        check_rss, interval, name=job_name, chat_id=chat_id, data=rss_data
    )


async def check_rss(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    rss_name, rss_feed, latest_handled_item_id = context.job.data
    info(f"Checking RSS in chat ID=[{chat_id}] for RSS=[{rss_name}]...")
    not_handled_feed_items = get_not_handled_feed_items(
        rss_feed, latest_handled_item_id
    )
    if not not_handled_feed_items:
        info(f"No new data for RSS=[{rss_name}] in chat ID=[{chat_id}]")
        return
    for unhandled_item in not_handled_feed_items:
        await send_rss_update(context, chat_id, rss_name, unhandled_item)
    latest_item_id = not_handled_feed_items[-1]["id"]
    update_rss_feed_in_db(chat_id, rss_feed, rss_name, latest_item_id)
    context.job.data = RssFeedData(rss_name, rss_feed, latest_item_id)


async def send_rss_update(context: ContextTypes.DEFAULT_TYPE, chat_id, rss_name, item):
    info(f"Sending message to ID=[{chat_id}]")
    item_id = item["id"]
    if "www.instagram.com" in item_id:
        await send_message_instagram(context, chat_id, rss_name, item)
    else:
        await send_message(context, chat_id, rss_name, item)
