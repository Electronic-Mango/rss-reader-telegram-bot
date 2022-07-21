"""
Module handling all RSS requests.
"""

from itertools import takewhile
from logging import getLogger

from dateutil.parser import parse as parse_date
from feedparser import parse
from feedparser.util import FeedParserDict

from settings import RSS_FEEDS

_logger = getLogger(__name__)


def get_parsed_feed(feed_type: str, feed_name: str) -> FeedParserDict:
    """Parse given feed type and feed name into FeedParserDict, based on URL from RSS links YAML."""
    feed_link = RSS_FEEDS[feed_type].format(source_pattern=feed_name)
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


def get_latest_id(feed: FeedParserDict) -> str:
    """Get latest ID for a given feed."""
    _logger.info(f"Getting latest ID for [{feed.href}]")
    entries = _get_sorted_entries(feed)
    return entries[0].id if entries else None


def get_not_handled_entries(feed: FeedParserDict, target_id: str) -> list[FeedParserDict]:
    """
    Get not yet handled entries for a given feed.
    Return all elements from the feed list, until element with ID matching the target ID.
    """
    _logger.info(f"Getting not handled entries for [{feed.href}] target ID [{target_id}]")
    entries = _get_sorted_entries(feed)
    not_handled_entries = takewhile(lambda entry: _not_latest_entry(target_id, entry.id), entries)
    not_handled_entries = list(not_handled_entries)
    not_handled_entries.reverse()
    return not_handled_entries


def _get_sorted_entries(feed: FeedParserDict) -> list[FeedParserDict]:
    return sorted(feed.entries, key=lambda entry: parse_date(entry.published), reverse=True)


def _not_latest_entry(target_id: str, entry_id: str) -> bool:
    return entry_id not in target_id and target_id not in entry_id
