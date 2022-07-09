from logging import getLogger

from feedparser.util import FeedParserDict
from telegram import Bot
from telegram.ext import ContextTypes, JobQueue

from db import get_feed_data_for_chat, get_latest_id_from_db, update_latest_id_in_db
from feed_parser import parse_entry
from feed_reader import get_not_handled_entries
from sender import send_update
from settings import LOOKUP_INTERVAL_SECONDS

_logger = getLogger(__name__)


def check_for_updates_repeatedly(
    job_queue: JobQueue,
    chat_id: int,
    feed_type: str,
    feed_name: str
) -> None:
    job_name = _check_updates_job_name(chat_id, feed_type, feed_name)
    # TODO When can this situation actually occur?
    if job_queue.get_jobs_by_name(job_name):
        _logger.warn(f"Update checker job=[{job_name}] is already started")
        return
    job_queue.run_repeating(
        callback=_check_for_updates,
        interval=LOOKUP_INTERVAL_SECONDS,
        name=job_name,
        chat_id=chat_id,
        data=(feed_type, feed_name),
    )


async def _check_for_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    feed_type, feed_name = context.job.data
    _logger.info(f"[{chat_id}] Checking for updates for [{feed_name}] [{feed_type}]")
    latest_id = get_latest_id_from_db(chat_id, feed_type, feed_name)
    not_handled_feed_entries = get_not_handled_entries(feed_type, feed_name, latest_id)
    if not not_handled_feed_entries:
        _logger.info(f"[{chat_id}] No new data for [{feed_name}] [{feed_type}]")
    else:
        await _handle_update(context.bot, chat_id, feed_type, feed_name, not_handled_feed_entries)


async def _handle_update(
    bot: Bot,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    not_handled_feed_entries: list[FeedParserDict]
) -> None:
    parsed_not_handled_entries = [parse_entry(entry) for entry in not_handled_feed_entries]
    for link, summary, media_urls in parsed_not_handled_entries:
        await send_update(bot, chat_id, feed_type, feed_name, link, summary, media_urls)
    latest_id = not_handled_feed_entries[-1].id
    update_latest_id_in_db(chat_id, feed_type, feed_name, latest_id)


def cancel_checking_for_chat(job_queue: JobQueue, chat_id: int) -> None:
    for feed_type, feed_name, _ in get_feed_data_for_chat(chat_id):
        cancel_checking_job(job_queue, chat_id, feed_type, feed_name)


def cancel_checking_job(
    job_queue: JobQueue,
    chat_id: int,
    feed_type: str,
    feed_name: str
) -> None:
    job_name = _check_updates_job_name(chat_id, feed_type, feed_name)
    jobs = job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    if len(jobs) > 1:
        _logger.warn(f"[{chat_id}] Found [{len(jobs)}] jobs with name [{job_name}]")


def _check_updates_job_name(chat_id: int, feed_type: str, feed_name: str) -> str:
    return f"check-updates-job-{chat_id}-{feed_type}-{feed_name}"
