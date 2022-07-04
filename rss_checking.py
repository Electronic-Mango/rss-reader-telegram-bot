from logging import getLogger
from os import getenv

from telegram.ext import ContextTypes, JobQueue

from db import RssFeedData, update_latest_item_id_in_db
from feed_item_sender_basic import send_message
from feed_item_sender_instagram import send_message_instagram
from feed_types import FeedTypes
from instagram_feed_reader import get_not_handled_feed_items

logger = getLogger(__name__)


def rss_checking_job_name(chat_id: str, rss_name: str):
    return f"check-rss-{chat_id}-{rss_name}"


def start_rss_checking(job_queue: JobQueue, chat_id: str, rss_data: RssFeedData):
    logger.info(str(rss_data))
    job_name = rss_checking_job_name(chat_id, rss_data.feed_name)
    if job_queue.get_jobs_by_name(job_name):
        logger.info(f"RSS checking job=[{job_name}] is already started.")
        return
    interval = int(getenv("LOOKUP_INTERVAL_SECONDS"))
    logger.info(
        f"Starting repeating job checking RSS for updates "
        f"with interval=[{interval}] "
        f"in chat ID=[{job_name}] "
        f"RSS=[{rss_data.feed_name}]"
    )
    job_queue.run_repeating(
        check_rss, interval, name=job_name, chat_id=chat_id, data=rss_data
    )


async def check_rss(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    rss_name, rss_type, rss_feed, latest_handled_item_id = context.job.data
    logger.info(f"Checking RSS in chat ID=[{chat_id}] for RSS=[{rss_name}]...")
    not_handled_feed_items = get_not_handled_feed_items(
        rss_feed, latest_handled_item_id
    )
    if not not_handled_feed_items:
        logger.info(f"No new data for RSS=[{rss_name}] in chat ID=[{chat_id}]")
        return
    for unhandled_item in not_handled_feed_items:
        await send_rss_update(context, chat_id, rss_name, rss_type, unhandled_item)
    latest_item_id = not_handled_feed_items[-1]["id"]
    update_latest_item_id_in_db(chat_id, rss_feed, rss_name, latest_item_id)
    context.job.data = RssFeedData(rss_name, rss_type, rss_feed, latest_item_id)


async def send_rss_update(context: ContextTypes.DEFAULT_TYPE, chat_id, rss_name, rss_type, item):
    logger.info(f"Sending message to ID=[{chat_id}]")
    if rss_type == FeedTypes.INSTAGRAM_TYPE:
        await send_message_instagram(context, chat_id, rss_name, item)
    else:
        await send_message(context, chat_id, rss_name, item)


def cancel_checking_job(context: ContextTypes.DEFAULT_TYPE, chat_id, feed_name):
    job_name = rss_checking_job_name(chat_id, feed_name)
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    if len(jobs) > 1:
        logger.warn(f"Found [{len(jobs)}] jobs with name [{job_name}]!")
