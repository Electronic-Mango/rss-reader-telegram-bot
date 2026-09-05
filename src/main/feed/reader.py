"""Module handling all RSS requests."""

from asyncio import to_thread
from datetime import datetime
from functools import partial
from itertools import takewhile
from time import struct_time

from feedparser import FeedParserDict, parse
from loguru import logger
from niquests import aget

from settings import RSS_FEEDS


async def get_parsed_feed(feed_type: str, feed_name: str) -> FeedParserDict:
    """Parse given information into FeedParserDict, based on URL from RSS links YAML."""
    feed_link = RSS_FEEDS[feed_type]["url"].format(source_pattern=feed_name)
    logger.info(f"Parsed [{feed_name}][{feed_type}] to link [{feed_link}]")
    feed_response = await aget(feed_link)
    # parse() only sets "status"/"href" when it performs the HTTP request itself.
    # Headers must be lowercased.
    # parse() header-based encoding detection expects lowercase keys.
    feed_content = feed_response.content
    headers = {k.lower(): v for k, v in feed_response.headers.items()}
    parsed_feed = await to_thread(parse, feed_content, response_headers=headers)
    parsed_feed["status"] = feed_response.status_code
    parsed_feed["href"] = feed_response.url
    return parsed_feed


def feed_is_valid(feed: FeedParserDict) -> bool:
    """
    Check whether a given feed is valid and can be used.

    There are multiple conditions which a feed response needs to match:
     - HTTP status code is either 200 or 301 (301 is a workaround for Tumblr blogs)
     - there are any feed items in the response
    Technically a feed can be valid, but without any items, when it was just created.
    This is a workaround for feeds which always respond with code 200.
    """
    logger.info(f"Checking if [{feed.href}] feed exists")
    # 301 is a workaround for Tumblr blogs with dedicated URLs.
    # Workaround for feeds which always respond with code 200.
    return feed.get("status") in [200, 301] and feed.get("entries")


def get_latest_data(feed: FeedParserDict) -> tuple[str, str, struct_time]:
    """Get data (entry ID, link, date) of latest entry for a given feed."""
    logger.info(f"Getting data from latest entry for [{feed.href}]")
    entries = get_sorted_entries(feed)
    latest_entry = entries[0]
    return get_data(latest_entry)


def get_data(entry: FeedParserDict) -> tuple[str, str, struct_time]:
    """Return data (entry ID, link, date) for a given entry."""
    entry_id = entry.get("id")
    link = entry.get("link")
    date = _get_entry_date(entry)
    return entry_id, link, date


def get_not_handled_entries(
    feed: FeedParserDict, target_id: str, date: struct_time | None
) -> list[FeedParserDict]:
    """
    Get not yet handled entries for a given feed.

    Return all elements from the list, until element with ID matching the target ID.
    """
    logger.info(f"Getting not handled entries for [{feed.href}] ID [{target_id}]")
    is_not_handled = partial(_not_latest_entry, target_id, date)
    not_handled_entries = list(takewhile(is_not_handled, get_sorted_entries(feed)))
    not_handled_entries.reverse()
    return not_handled_entries


def get_sorted_entries(feed: FeedParserDict) -> list[FeedParserDict]:
    if not (entries := feed.get("entries")):
        return []
    return sorted(entries, key=_get_entry_date, reverse=True)


def _not_latest_entry(
    latest_id: str, latest_date: struct_time | None, entry: FeedParserDict
) -> bool:
    id_is_not_latest = latest_id is None or entry.get("id") != latest_id
    entry_date = _get_entry_date(entry)
    date_is_newer = entry_date > latest_date if entry_date and latest_date else True
    return id_is_not_latest and date_is_newer


def _get_entry_date(entry: FeedParserDict) -> struct_time:
    return (
        entry.get("published_parsed")
        or entry.get("updated_parsed")
        or datetime.min.timetuple()
    )
