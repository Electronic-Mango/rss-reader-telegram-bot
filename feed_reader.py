from itertools import takewhile
from logging import getLogger

from dateutil.parser import parse as parse_date
from feedparser import parse
from feedparser.util import FeedParserDict

_logger = getLogger(__name__)


def get_latest_feed_entry_id(feed_link: str) -> str:
    _logger.info(f"Getting latest ID for [{feed_link}]")
    entries = _get_sorted_feed_entries(feed_link)
    if not entries:
        return None
    return entries[-1]["id"]


def get_not_handled_feed_entries(feed_link: str, target_id: str) -> list[FeedParserDict]:
    _logger.info(f"Getting not handled entries for [{feed_link}]")
    entries = _get_sorted_feed_entries(feed_link)
    if target_id is None:
        return entries
    # TODO Clean this part up, there's no need for double-reverse
    entries.reverse()
    not_handled_entries = takewhile(lambda entry: entry.id != target_id, entries)
    not_handled_entries = list(not_handled_entries)
    not_handled_entries.reverse()
    return not_handled_entries


def feed_exists(feed_link: str) -> bool:
    _logger.info(f"Checking if [{feed_link}] is a valid link")
    # 301 is a workaround for tumblr blogs with dedicated URLs
    return parse(feed_link)["status"] in [200, 301]


def _get_sorted_feed_entries(feed_link: str) -> list[FeedParserDict]:
    entries = parse(feed_link)["entries"]
    return sorted(entries, key=lambda entry: parse_date(entry["published"]))
