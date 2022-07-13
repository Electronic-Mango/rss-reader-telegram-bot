from logging import getLogger

from feedparser.util import FeedParserDict
from telegram import Bot
from telegram.ext import ContextTypes, JobQueue

from db import get_all_stored_data, update_stored_latest_id
from feed_parser import parse_entry
from feed_reader import get_not_handled_entries
from sender import send_update
from settings import (
    LOOKUP_FEED_DELAY_SECONDS,
    LOOKUP_INITIAL_DELAY_SECONDS,
    LOOKUP_INTERVAL_SECONDS,
)

_logger = getLogger(__name__)


def start_checking_for_updates(job_queue: JobQueue) -> None:
    _logger.info("Starting checking for updates...")
    job_queue.run_repeating(
        callback=_check_for_all_updates,
        interval=LOOKUP_INTERVAL_SECONDS,
        first=LOOKUP_INITIAL_DELAY_SECONDS,
    )


async def _check_for_all_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    _logger.info("Starting checking for all updates")
    for delay, feed_data in enumerate(get_all_stored_data()):
        context.job_queue.run_once(
            callback=_check_for_updates,
            when=delay * LOOKUP_FEED_DELAY_SECONDS,
            data=feed_data,
        )


async def _check_for_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, feed_type, feed_name, latest_id = context.job.data
    _logger.info(f"[{chat_id}] Checking for updates for [{feed_name}] [{feed_type}]")
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
    not_handled_feed_entries: list[FeedParserDict],
) -> None:
    _logger.info(f"[{chat_id}] Handling update [{feed_name}] [{feed_type}]")
    parsed_not_handled_entries = [parse_entry(entry) for entry in not_handled_feed_entries]
    for link, summary, media_urls in parsed_not_handled_entries:
        await send_update(bot, chat_id, feed_type, feed_name, link, summary, media_urls)
    latest_id = not_handled_feed_entries[-1].id
    update_stored_latest_id(chat_id, feed_type, feed_name, latest_id)
