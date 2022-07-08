from itertools import takewhile
from logging import getLogger

from dateutil.parser import parse as parse_date
from feedparser import parse
from feedparser.util import FeedParserDict
from settings import RSS_FEEDS

_logger = getLogger(__name__)


def get_latest_entry_id(feed_type: str, feed_name: str) -> str:
    _logger.info(f"Getting latest ID for [{feed_name}] [{feed_type}]")
    entries = _get_sorted_entries(feed_type, feed_name)
    if not entries:
        return None
    return entries[-1]["id"]


def get_not_handled_entries(feed_type: str, feed_name: str, target_id: str) -> list[FeedParserDict]:
    _logger.info(f"Getting not handled entries for [{feed_name}] [{feed_type}]")
    entries = _get_sorted_entries(feed_type, feed_name)
    if target_id is None:
        return entries
    # TODO Clean this part up, there's no need for double-reverse
    entries.reverse()
    not_handled_entries = takewhile(lambda entry: entry.id != target_id, entries)
    not_handled_entries = list(not_handled_entries)
    not_handled_entries.reverse()
    return not_handled_entries


def feed_exists(feed_type: str, feed_name: str) -> bool:
    _logger.info(f"Checking if [{feed_name}] [{feed_type}] feed exists")
    # 301 is a workaround for tumblr blogs with dedicated URLs
    return _get_parsed_feed(feed_type, feed_name)["status"] in [200, 301]


def _get_sorted_entries(feed_type: str, feed_name: str) -> list[FeedParserDict]:
    entries = _get_parsed_feed(feed_type, feed_name)["entries"]
    return sorted(entries, key=lambda entry: parse_date(entry["published"]))


def _get_parsed_feed(feed_type: str, feed_name: str) -> FeedParserDict:
    feed_link = _get_feed_link(feed_type, feed_name)
    _logger.info(f"Parsed [{feed_name}][{feed_type}] to link [{feed_link}]")
    return parse(feed_link)


# TODO Perhaps it would be worth it to store feed link in jobs, but not in DB?
# This way there would be no need to parse it every time.
def _get_feed_link(feed_type: str, feed_name: str) -> str:
    return RSS_FEEDS[feed_type].format(source_pattern=feed_name)
