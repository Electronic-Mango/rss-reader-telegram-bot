from logging import getLogger

from telegram.error import Forbidden
from telegram.ext import ContextTypes, JobQueue

from db import remove_chat_data, update_latest_id_in_db
from feed_parser import parse_entry
from feed_reader import get_not_handled_entries
from sender import send_update
from settings import LOOKUP_INTERVAL_SECONDS

_logger = getLogger(__name__)


def check_for_updates_repeatedly(
    job_queue: JobQueue,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    latest_id: str
) -> None:
    job_name = _check_updates_job_name(chat_id, feed_type, feed_name)
    if job_queue.get_jobs_by_name(job_name):
        _logger.info(f"Update checker job=[{job_name}] is already started")
        return
    job_queue.run_repeating(
        callback=_check_for_updates,
        interval=LOOKUP_INTERVAL_SECONDS,
        name=job_name,
        chat_id=chat_id,
        data=(feed_type, feed_name, latest_id),
    )


async def _check_for_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = context.job.chat_id
    feed_type, feed_name, latest_id = context.job.data
    _logger.info(f"[{chat_id}] Checking for updates for [{feed_name}] [{feed_type}]")
    not_handled_feed_entries = get_not_handled_entries(feed_type, feed_name, latest_id)
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
    latest_id = not_handled_feed_entries[-1].id
    update_latest_id_in_db(chat_id, feed_type, feed_name, latest_id)
    # TODO Is there a better way of handing this, than to overwrite the whole job data?
    context.job.data = (feed_type, feed_name, latest_id)


# TODO Is this the best way of handling user removing and blocking the bot?
def remove_chat_and_job(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    _logger.warn(f"[{chat_id}] Couldn't send updates, removing from DB and stopping jobs")
    remove_chat_data(chat_id)
    chat_jobs = [
        job for job in context.job_queue.jobs()
        if job.name.startswith(_update_checker_job_name_chat_prefix(chat_id))
    ]
    for job in chat_jobs:
        job.schedule_removal()


# TODO If it was the last job, then remove everything from the DB
def cancel_checking_job(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    feed_type: str,
    feed_name: str
) -> None:
    job_name = _check_updates_job_name(chat_id, feed_type, feed_name)
    jobs = context.job_queue.get_jobs_by_name(job_name)
    for job in jobs:
        job.schedule_removal()
    if len(jobs) > 1:
        _logger.warn(f"[{chat_id}] Found [{len(jobs)}] jobs with name [{job_name}]")


def _check_updates_job_name(chat_id: int, feed_type: str, feed_name: str) -> str:
    return f"{_update_checker_job_name_chat_prefix(chat_id)}{feed_type}-{feed_name}"


def _update_checker_job_name_chat_prefix(chat_id: int) -> str:
    return f"check-updates-{chat_id}-"
