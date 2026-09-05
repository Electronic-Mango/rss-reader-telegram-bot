"""
Module responsible for checking for RSS updates.

Information about which RSS items should be checked is extracted from a DB.

Each item will then be scheduled for update in a separate job.
Created jobs have staggered trigger times, to avoid bottlenecks,
where too many simultaneous messages are send to a chat.

Accessing DB, reading and parsing the RSS feed and sending updates to chats
is handled in separate modules.
"""

from asyncio import Task, current_task, sleep
from datetime import datetime
from random import randrange, shuffle
from time import struct_time

from feedparser import FeedParserDict
from loguru import logger
from telegram import Bot
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from bot.sender import send_update
from db.wrapper import (
    get_all_stored_data,
    remove_stored_chat_data,
    update_latest_message_id,
    update_stored_latest_data,
)
from feed.parser import parse_description, parse_link, parse_media_links, parse_title
from feed.reader import feed_is_valid, get_data, get_not_handled_entries, get_parsed_feed
from settings import (
    LOOKUP_FEED_DELAY,
    LOOKUP_FEED_DELAY_RANDOMNESS,
    LOOKUP_INTERVAL_RANDOMNESS,
    QUIET_HOURS,
    SHUFFLE_UPDATES,
)

_active_update_check: Task[None] | None = None


def cancel_active_update_check() -> None:
    if _active_update_check is not None and not _active_update_check.done():
        logger.info("Cancelling active update check")
        _active_update_check.cancel()


async def check_for_all_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    global _active_update_check
    _active_update_check = current_task()
    try:
        if initial_delay := randrange(max(LOOKUP_INTERVAL_RANDOMNESS, 1)):
            logger.info(f"Delaying checking for updates for [{initial_delay}] seconds")
            await sleep(initial_delay)
        await _delayed_check_for_all_updates(context)
        logger.info("Finished checking for all updates")
    except Exception as e:
        logger.opt(exception=e).error("Error occured during update job: ")
    finally:
        _active_update_check = None


async def _delayed_check_for_all_updates(context: ContextTypes.DEFAULT_TYPE) -> None:
    if datetime.now().hour in QUIET_HOURS:
        logger.info("Quiet hour, skipping checking for updates")
        return
    logger.info("Starting checking for all updates")
    all_data = await get_all_stored_data()
    if SHUFFLE_UPDATES:
        logger.info("Shuffling RSS data before checking for updates")
        shuffle(all_data)
    for chat_id, feed_type, feed_name, latest_id, latest_date, latest_message_id in all_data:
        context.job.chat_id = chat_id
        context.job.data = feed_type, feed_name
        try:
            await _check_for_updates(
                context.bot,
                chat_id,
                feed_type,
                feed_name,
                latest_id,
                latest_date,
                latest_message_id,
            )
        except Forbidden:
            logger.warning(f"[{chat_id}] Cannot send updates to chat, removing chat data")
            await remove_stored_chat_data(chat_id)
        except Exception as e:
            logger.opt(exception=e).error(
                f"[{chat_id}] Unexpected error occurred during update check for "
                f"[{feed_name}] [{feed_type}]: "
            )
        await sleep(LOOKUP_FEED_DELAY + randrange(max(LOOKUP_FEED_DELAY_RANDOMNESS, 1)))


async def _check_for_updates(
    bot: Bot,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    latest_id: str,
    latest_date: struct_time | None,
    latest_message_id: int | None,
) -> None:
    logger.info(f"[{chat_id}] Checking for updates for [{feed_name}] [{feed_type}]")
    if not feed_is_valid(feed := await get_parsed_feed(feed_type, feed_name)):
        logger.error(f"Feed for [{feed_name}] [{feed_type}] is not valid anymore")
        return
    if not (not_handled := get_not_handled_entries(feed, latest_id, latest_date)):
        logger.info(f"[{chat_id}] No new data for [{feed_name}] [{feed_type}]")
        return
    try:
        await _handle_update(bot, chat_id, feed_type, feed_name, not_handled, latest_message_id)
    except Exception as e:
        logger.opt(exception=e).warning(f"[{chat_id}] Error occurred when handling previous one: ")
        await bot.send_message(
            chat_id, f"Error occurred when handling a previous error:\n{e}", parse_mode=None
        )


async def _handle_update(
    bot: Bot,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    not_handled_feed_entries: list[FeedParserDict],
    latest_message_id: int | None,
) -> None:
    logger.info(f"[{chat_id}] Handling update [{feed_name}] [{feed_type}]")
    for entry in not_handled_feed_entries:
        entry_id, link, date = get_data(entry)
        await update_stored_latest_data(chat_id, feed_type, feed_name, entry_id, link, date)
        latest_message_id = await _send_update(
            bot, chat_id, feed_type, feed_name, entry, latest_message_id
        )
        await update_latest_message_id(chat_id, feed_type, feed_name, latest_message_id)
        await sleep(1)  # Small delay to avoid hitting the bot/sources too hard


async def _send_update(
    bot: Bot,
    chat_id: int,
    feed_type: str,
    feed_name: str,
    entry: FeedParserDict,
    latest_message_id: int | None,
) -> int:
    link = parse_link(entry)
    title = parse_title(entry, feed_type)
    description = parse_description(entry, feed_type)
    media = parse_media_links(entry)
    base_send_args = bot, chat_id, feed_type, feed_name, link, title, description, latest_message_id
    try:
        return await send_update(*base_send_args, media)
    except Exception as e:
        logger.opt(exception=e).warning(f"[{chat_id}] Trying to resend data without media due to: ")
        return await send_update(*base_send_args)
