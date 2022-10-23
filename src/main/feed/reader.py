"""
Module handling all RSS requests.
"""

from itertools import takewhile
from logging import getLogger
from time import struct_time

from feedparser import parse
from feedparser.util import FeedParserDict

from settings import RSS_FEEDS

_logger = getLogger(__name__)


def get_parsed_feed(feed_type: str, feed_name: str) -> FeedParserDict:
    """Parse given feed type and feed name into FeedParserDict, based on URL from RSS links YAML."""
    feed_link = RSS_FEEDS[feed_type]["url"].format(source_pattern=feed_name)
    _logger.info(f"Parsed [{feed_name}][{feed_type}] to link [{feed_link}]")
    return parse(feed_link)


def feed_is_valid(feed: FeedParserDict) -> bool:
    """
    Check whether a given feed is valid and can be used.

    There are multiple conditions which a feed response needs to match:
     - HTTP status code is either 200 or 301 (301 is a workaround for Tumblr blogs)
     - there are any feed items in the response
    Technically a feed can be valid, but without any items, when it was just created.
    Checking for those items is an workaround for feeds which always responde with code 200.
    """
    _logger.info(f"Checking if [{feed.href}] feed exists")
    # 301 is a workaround for Tumblr blogs with dedicated URLs.
    # Checking for any entries is a workaround for feeds which always respond with code 200.
    return feed.status in [200, 301] and "entries" in feed and feed.entries


def get_latest_data(feed: FeedParserDict) -> tuple[str, str, struct_time]:
    """Get data (entry ID, link, date) of latest entry for a given feed"""
    _logger.info(f"Getting data from latest entry for [{feed.href}]")
    entries = _get_sorted_entries(feed)
    latest_entry = entries[0]
    return get_data(latest_entry)


def get_data(entry: FeedParserDict) -> tuple[str, str, struct_time]:
    """Return data (entry ID, link, data) for a given entry"""
    id = entry.get("id")
    link = entry.get("link")
    date = entry.get("published_parsed") or entry.get("published_parsed")
    return id, link, date


def get_not_handled_entries(
    feed: FeedParserDict, id: str, date: struct_time
) -> list[FeedParserDict]:
    """
    Get not yet handled entries for a given feed.
    Return all elements from the feed list, until element with ID matching the target ID.
    """
    _logger.info(f"Getting not handled entries for [{feed.href}] target ID [{id}]")
    entries = _get_sorted_entries(feed)
    not_handled_entries = takewhile(lambda entry: _not_latest_entry(id, date, entry), entries)
    not_handled_entries = list(not_handled_entries)
    not_handled_entries.reverse()
    return not_handled_entries


def _get_sorted_entries(feed: FeedParserDict) -> list[FeedParserDict]:
    return sorted(feed.entries, key=lambda entry: entry.get("published_parsed"), reverse=True)


def _not_latest_entry(latest_id: str, latest_date: struct_time, entry: FeedParserDict) -> bool:
    entry_id_is_not_latest = entry.id not in latest_id and latest_id not in entry.id
    entry_date = entry.get("published_parsed")
    entry_date_is_newer = entry_date > latest_date if entry_date else True
    return entry_id_is_not_latest and entry_date_is_newer
