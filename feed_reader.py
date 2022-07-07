from itertools import takewhile

from dateutil.parser import parse as parse_date
from feedparser import parse


def get_latest_feed_entry_id(feed_link):
    entries = _get_sorted_feed_entries(feed_link)
    if not entries:
        return None
    return entries[-1]["id"]


def get_not_handled_feed_entries(feed_link, target_id):
    entries = _get_sorted_feed_entries(feed_link)
    if target_id is None:
        return entries
    # TODO Clean this part up, there's no need for double-reverse
    entries.reverse()
    not_handled_entries = takewhile(lambda entry: entry.id != target_id, entries)
    not_handled_entries = list(not_handled_entries)
    not_handled_entries.reverse()
    return not_handled_entries


def feed_exists(feed_link):
    # 301 is a workaround for tumblr blogs with dedicated URLs
    return parse(feed_link)["status"] in [200, 301]


def _get_sorted_feed_entries(feed_link):
    entries = parse(feed_link)["entries"]
    return sorted(entries, key=lambda entry: parse_date(entry["published"]))
