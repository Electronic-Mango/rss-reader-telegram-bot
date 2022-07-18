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


def feed_is_valid(feed_type: str, feed_name: str) -> bool:
    """
    Check whether a given feed is valid and can be used.

    There are multiple conditions which a feed response needs to match:
     - HTTP status code is either 200 or 301 (301 is a workaround for Tumblr blogs)
     - there are any feed items in the response
    Technically a feed can be valid, but without any items, when it was just created.
    Checking for those items is an workaround for feeds which always responde with code 200.
    """
    _logger.info(f"Checking if [{feed_name}] [{feed_type}] feed exists")
    feed = _get_parsed_feed(feed_type, feed_name)
    # 301 is a workaround for Tumblr blogs with dedicated URLs.
    # Checking for any entries is a workaround for feeds which always respond with code 200.
    return feed["status"] in [200, 301] and "entries" in feed and feed["entries"]


def get_latest_id(feed_type: str, feed_name: str) -> str:
    """Get latest ID for a given feed."""
    _logger.info(f"Getting latest ID for [{feed_name}] [{feed_type}]")
    entries = _get_sorted_entries(feed_type, feed_name)
    return entries[0]["id"] if entries else None


def get_not_handled_entries(feed_type: str, feed_name: str, target_id: str) -> list[FeedParserDict]:
    """
    Get not yet handled entries for a given feed.
    Return all elements from the feed list, until element with ID matching the target ID.
    """
    _logger.info(f"Getting not handled entries for [{feed_name}] [{feed_type}]")
    entries = _get_sorted_entries(feed_type, feed_name)
    not_handled_entries = takewhile(lambda entry: _not_latest_entry(target_id, entry.id), entries)
    not_handled_entries = list(not_handled_entries)
    not_handled_entries.reverse()
    return not_handled_entries


def _get_sorted_entries(feed_type: str, feed_name: str) -> list[FeedParserDict]:
    parsed_feed = _get_parsed_feed(feed_type, feed_name)
    entries = parsed_feed["entries"]
    return sorted(entries, key=lambda entry: parse_date(entry["published"]), reverse=True)


def _get_parsed_feed(feed_type: str, feed_name: str) -> FeedParserDict:
    feed_link = RSS_FEEDS[feed_type].format(source_pattern=feed_name)
    _logger.info(f"Parsed [{feed_name}][{feed_type}] to link [{feed_link}]")
    return parse(feed_link)


def _not_latest_entry(target_id: str, entry_id: str) -> bool:
    return entry_id not in target_id and target_id not in entry_id
