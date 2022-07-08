from logging import getLogger

from telegram.error import Forbidden
from telegram.ext import ContextTypes, JobQueue

from db import RssFeedData, remove_chat_collection, update_latest_item_id_in_db
from feed_parser import parse_entry
from feed_reader import get_not_handled_feed_entries
from sender import send_update
from settings import LOOKUP_INTERVAL_SECONDS

_logger = getLogger(__name__)


def start_rss_checking(job_queue: JobQueue, chat_id: str, feed_data: RssFeedData) -> None:
    job_name = _rss_checking_job_name(chat_id, feed_data.feed_type, feed_data.feed_name)
    # TODO This check might not be necessary now,
    # subscriptions shouldn't be duplicated in DB,
    # user cannot add the same subscription twice.
    if job_queue.get_jobs_by_name(job_name):
        _logger.info(f"RSS checking job=[{job_name}] is already started.")
        return
    job_queue.run_repeating(
        callback=_check_for_updates,
        interval=LOOKUP_INTERVAL_SECONDS,
        name=job_name,
        chat_id=chat_id,
        data=feed_data,
    )


async def _check_for_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    feed_name, feed_type, feed_link, latest_id = context.job.data
    _logger.info(f"[{chat_id}] Checking for updates for [{feed_name}] [{feed_type}]")
    not_handled_feed_entries = get_not_handled_feed_entries(feed_link, latest_id)
    if not not_handled_feed_entries:
        _logger.info(f"[{chat_id}] No new data for [{feed_name}] [{feed_type}]")
        return
    # TODO Clean up handling errors
    for parsed_entry in [parse_entry(entry) for entry in not_handled_feed_entries]:
        try:
            await send_update(context, chat_id, feed_type, feed_name, parsed_entry)
        except Forbidden:
            remove_chat_and_job(context, chat_id)
            return
    latest_entry_id = not_handled_feed_entries[-1].id
    update_latest_item_id_in_db(chat_id, feed_type, feed_name, latest_entry_id)
    context.job.data = RssFeedData(feed_name, feed_type, feed_link, latest_entry_id)


# TODO Is this the best way of handling user removing and blocking the bot?
def remove_chat_and_job(context: ContextTypes.DEFAULT_TYPE, chat_id: str) -> None:
    _logger.warn(f"[{chat_id}] Couldn't send updates, removing from DB and stopping jobs")
    remove_chat_collection(chat_id)
    chat_jobs = [
        job for job in context.job_queue.jobs()
        if job.name.startswith(_rss_checking_job_name_chat_prefix(chat_id))
    ]
    for job in chat_jobs:
        job.schedule_removal()


# TODO If it was the last job, then remove everything from the DB
def cancel_checking_job(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: str,
    feed_type: str,
    feed_name: str
) -> None:
    job_name = _rss_checking_job_name(chat_id, feed_type, feed_name)
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    if len(jobs) > 1:
        _logger.warn(f"[{chat_id}] Found [{len(jobs)}] jobs with name [{job_name}]")


def _rss_checking_job_name(chat_id: str, feed_type: str, feed_name: str) -> str:
    return f"{_rss_checking_job_name_chat_prefix(chat_id)}{feed_type}-{feed_name}"


def _rss_checking_job_name_chat_prefix(chat_id: str) -> str:
    return f"check-rss-{chat_id}-"
