from logging import getLogger

from telegram.error import Forbidden
from telegram.ext import ContextTypes, JobQueue

from db import RssFeedData, remove_chat_collection, update_latest_item_id_in_db
from feed_parser import parse_entry
from feed_reader import get_not_handled_feed_entries
from sender import send_message
from settings import LOOKUP_INTERVAL_SECONDS

_logger = getLogger(__name__)


def start_rss_checking(job_queue: JobQueue, chat_id: str, feed_data: RssFeedData):
    job_name = _rss_checking_job_name(chat_id, feed_data.feed_type, feed_data.feed_name)
    # TODO This check might not be necessary now,
    # subscriptions shouldn't be duplicated in DB,
    # user cannot add the same subscription twice.
    if job_queue.get_jobs_by_name(job_name):
        _logger.info(f"RSS checking job=[{job_name}] is already started.")
        return
    interval = LOOKUP_INTERVAL_SECONDS
    _logger.info(
        f"Starting repeating job checking RSS for updates "
        f"with interval=[{interval}] "
        f"in chat ID=[{job_name}] "
        f"RSS=[{feed_data.feed_name}]"
    )
    job_queue.run_repeating(
        check_rss, interval, name=job_name, chat_id=chat_id, data=feed_data
    )


async def check_rss(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    feed_name, feed_type, feed_link, latest_id = context.job.data
    _logger.info(f"Checking RSS in chat ID=[{chat_id}] for RSS=[{feed_name}]...")
    not_handled_feed_entries = get_not_handled_feed_entries(feed_link, latest_id)
    if not not_handled_feed_entries:
        _logger.info(f"No new data for RSS=[{feed_name}] in chat ID=[{chat_id}]")
        return
    for parsed_entry in [parse_entry(entry) for entry in not_handled_feed_entries]:
        try:
            await send_message(context, chat_id, feed_type, feed_name, parsed_entry)
        except Forbidden:
            remove_chat_and_job(context, chat_id)
            return
    latest_entry_id = not_handled_feed_entries[-1].id
    update_latest_item_id_in_db(chat_id, feed_type, feed_name, latest_entry_id)
    context.job.data = RssFeedData(feed_name, feed_type, feed_link, latest_entry_id)


 # TODO Is this the best way of handling user removing and blocking the bot?
def remove_chat_and_job(context: ContextTypes.DEFAULT_TYPE, chat_id):
    _logger.warn(f"Couldn't send updates to chat ID=[{chat_id}]!")
    _logger.warn(f"Removing from DB chat ID=[{chat_id}] and stopping job queue!")
    remove_chat_collection(chat_id)
    for job in context.job_queue.jobs():
        if job.name.startswith(_rss_checking_job_name_chat_prefix(chat_id)):
            job.schedule_removal()


def cancel_checking_job(context: ContextTypes.DEFAULT_TYPE, chat_id, feed_type, feed_name):
    job_name = _rss_checking_job_name(chat_id, feed_type, feed_name)
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    if len(jobs) > 1:
        _logger.warn(f"Found [{len(jobs)}] jobs with name [{job_name}]!")


def _rss_checking_job_name(chat_id, feed_type, feed_name):
    return f"{_rss_checking_job_name_chat_prefix(chat_id)}{feed_type}-{feed_name}"


def _rss_checking_job_name_chat_prefix(chat_id):
    return f"check-rss-{chat_id}-"
