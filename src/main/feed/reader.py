"""Module handling all RSS requests."""

from asyncio import to_thread
from collections.abc import Generator
from datetime import datetime
from functools import partial
from itertools import takewhile
from re import match
from time import struct_time

from feedparser import parse
from loguru import logger
from niquests import aget

from feed.types import RssEntry, RssFeed
from feed.utils import format_date, get_entry_date
from settings import Settings


async def get_parsed_feed(feed_type: str, feed_name: str) -> RssFeed:
    """Parse given information into RssFeed, based on URL from RSS links YAML."""
    feed_link = Settings.RSS_FEEDS[feed_type]["url"].format(source_pattern=feed_name)
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
    parsed_feed["feed_type"] = feed_type
    parsed_feed["feed_name"] = feed_name
    return parsed_feed


def feed_is_valid(feed: RssFeed) -> bool:
    """
    Check whether a given feed is valid and can be used.

    There are multiple conditions which a feed response needs to match:
     - HTTP status code is either 200 or 301 (301 is a workaround for Tumblr blogs)
     - there are any feed items in the response
    Technically a feed can be valid, but without any items, when it was just created.
    This is a workaround for feeds which always respond with code 200.
    """
    logger.info(f"Checking if [{feed.get('href')}] feed exists")
    # 301 is a workaround for Tumblr blogs with dedicated URLs.
    # Workaround for feeds which always respond with code 200.
    return feed.get("status") in [200, 301] and any(_get_usable_entries(feed))


def get_latest_data(feed: RssFeed) -> tuple[str, str | None, struct_time | None]:
    """Get data (entry ID, link, date) of latest entry for a given feed."""
    logger.info(f"Getting data from latest entry for [{feed.get('href')}]")
    entries = get_sorted_entries(feed)
    latest_entry = entries[0]
    return get_data(latest_entry)


def get_data(entry: RssEntry) -> tuple[str, str | None, struct_time | None]:
    """Return data (entry ID, link, date) for a given entry."""
    entry_id = entry["id"]  # Entries without IDs are already rejected
    link = entry.get("link")
    date = get_entry_date(entry)
    return entry_id, link, date


def get_not_handled_entries(
    feed: RssFeed, target_id: str, date: struct_time | None
) -> list[RssEntry]:
    """
    Get not yet handled entries for a given feed.

    Return all elements from the list, until element with ID matching the target ID.
    """
    logger.info(f"Getting not handled entries for [{feed.get('href')}] [{target_id}]")
    is_not_handled = partial(_not_latest_entry, target_id, date)
    not_handled_entries = list(takewhile(is_not_handled, get_sorted_entries(feed)))
    not_handled_entries.reverse()
    return not_handled_entries


def get_sorted_entries(feed: RssFeed) -> list[RssEntry]:
    """Return all valid entries for a given feed, sorted by date in descending order."""
    return sorted(
        _get_usable_entries(feed),
        key=lambda entry: get_entry_date(entry) or datetime.min.timetuple(),
        reverse=True,
    )


def _get_usable_entries(feed: RssFeed) -> Generator[RssEntry]:
    """Return all usable entries for a given feed."""
    return (
        entry
        for entry in feed.get("entries", [])
        if _entry_is_valid(entry, feed.get("feed_type"))
    )


def _entry_is_valid(entry: RssEntry, feed_type: str | None) -> bool:
    """
    Check if the entry is a valid RSS update.

    Entries are considered valid if:
     - The entry has a non-empty ID.
     - The entry matches all specified RSS type-specific filters (if any).
    """
    if not entry.get("id"):
        return False
    if not (filters := Settings.RSS_FEEDS.get(feed_type, {}).get("entry_filters")):
        return True
    # With default empty string the regular inclusion patterns fail (since there
    # is nothing that can match), but negative-lookahead exclusion patterns pass
    # (since they don't appear in the empty string).
    logger.info(f"Applying filters: [{filters}]")
    return all(
        match(regex, entry.get(field, ""))
        for field, regex in filters.items()
        if field and regex
    )


def _not_latest_entry(
    latest_id: str, latest_date: struct_time | None, entry: RssEntry
) -> bool:
    """Check if the given entry is not the latest entry based on ID and date."""
    id_is_not_latest = (entry_id := entry.get("id")) != latest_id
    entry_date = get_entry_date(entry)
    date_is_newer = entry_date > latest_date if entry_date and latest_date else True
    logger.info(
        "Checking for latest entry "
        f"latest_id=[{latest_id}] latest_date=[{format_date(latest_date)}] "
        f"against entry_id=[{entry_id}] entry_date=[{format_date(entry_date)}] "
        f"id_is_not_latest=[{id_is_not_latest}] date_is_newer=[{date_is_newer}] "
        f"returning=[{id_is_not_latest and date_is_newer}]"
    )
    return id_is_not_latest and date_is_newer
