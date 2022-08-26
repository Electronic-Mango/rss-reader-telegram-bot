"""
Module responsible for checking for RSS updates.

Information about which RSS items should be checked is extracted from a DB.

Each item will then be scheduled for update in a separate job.
Created jobs have staggered trigger times, to avoid bottlenecks,
where too many simultaneous messages are send to a chat.

Accessing DB, reading and parsing the RSS feed and sending updates to chats
is handled in separate modules.
"""

from datetime import datetime
from logging import getLogger
from random import randrange

from feedparser.util import FeedParserDict
from telegram import Bot
from telegram.ext import ContextTypes

from bot.sender import send_update
from db.wrapper import get_all_stored_data, update_stored_latest_data
from feed.parser import parse_description, parse_link, parse_media_links, parse_title
from feed.reader import feed_is_valid, get_data, get_not_handled_entries, get_parsed_feed
from settings import (
    LOOKUP_FEED_DELAY,
    LOOKUP_FEED_DELAY_RANDOMNESS,
    LOOKUP_INTERVAL_RANDOMNESS,
    QUIET_HOURS,
)

_logger = getLogger(__name__)


async def check_for_all_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    lookup_interval = randrange(max(LOOKUP_INTERVAL_RANDOMNESS, 1))  # randrange(1) always returns 0
    _logger.info(f"Delaying checking for updates for [{lookup_interval}] seconds")
    context.job_queue.run_once(callback=_delayed_check_for_all_updates, when=lookup_interval)


async def _delayed_check_for_all_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    if datetime.now().hour in QUIET_HOURS:
        _logger.info("Quiet hour, skipping checking for updates")
        return
    _logger.info("Starting checking for all updates")
    delay = 0
    for feed_data in get_all_stored_data():
        context.job_queue.run_once(callback=_check_for_updates, when=delay, data=feed_data)
        delay += LOOKUP_FEED_DELAY
        delay += randrange(max(LOOKUP_FEED_DELAY_RANDOMNESS, 1))  # randrange(1) always returns 0


async def _check_for_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id, feed_type, feed_name, latest_id = context.job.data
    _logger.info(f"[{chat_id}] Checking for updates for [{feed_name}] [{feed_type}]")
    feed = get_parsed_feed(feed_type, feed_name)
    if feed_is_valid(feed):
        await _check_for_new_entries(context.bot, chat_id, feed, feed_type, feed_name, latest_id)
    else:
        _logger.error(f"Feed for [{feed_name}] [{feed_type}] is not valid anymore")


async def _check_for_new_entries(
    bot: Bot, chat_id: int, feed: FeedParserDict, feed_type: str, feed_name: str, latest_id: str
) -> None:
    not_handled_feed_entries = get_not_handled_entries(feed, latest_id)
    if not_handled_feed_entries:
        await _handle_update(bot, chat_id, feed_type, feed_name, not_handled_feed_entries)
    else:
        _logger.info(f"[{chat_id}] No new data for [{feed_name}] [{feed_type}]")


async def _handle_update(
    bot: Bot,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    not_handled_feed_entries: list[FeedParserDict],
) -> None:
    _logger.info(f"[{chat_id}] Handling update [{feed_name}] [{feed_type}]")
    for entry in not_handled_feed_entries:
        link = parse_link(entry)
        title = parse_title(entry, feed_type)
        description = parse_description(entry, feed_type)
        media_links = parse_media_links(entry)
        await send_update(bot, chat_id, feed_type, feed_name, link, title, description, media_links)
    id, link, date = get_data(not_handled_feed_entries[-1])
    update_stored_latest_data(chat_id, feed_type, feed_name, id, link, date)
