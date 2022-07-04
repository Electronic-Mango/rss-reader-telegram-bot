from collections import namedtuple
from feedparser import parse
from itertools import takewhile

FeedEntry = namedtuple("FeedEntry", ["id", "url", "summary", "media"])
FeedMedia = namedtuple("FeedMedia", ["url", "type"])


def get_latest_feed_entry_id(feed_link):
    entries = _get_feed_entries(feed_link)
    if not entries:
        return None
    return entries[0].id


def get_not_handled_feed_entries(feed_link, target_id):
    entries = _get_feed_entries(feed_link)
    if target_id is None:
        return entries
    not_handled_entries = takewhile(lambda entry: entry.id != target_id, entries)
    not_handled_entries = list(not_handled_entries)
    not_handled_entries.reverse()
    return not_handled_entries


def feed_exists(feed_link):
    feed = parse(feed_link)
    # 301 is a workaround for tumblr blogs with dedicated URLs
    if feed["status"] not in [200, 301]:
        return False
    # Workaround for Instagram feed
    entries = feed["entries"]
    return len(entries) != 1 or "Bridge returned error 500!" not in entries[0]["title"]


def _get_feed_entries(feed_link):
    entries = parse(feed_link)["entries"]
    parsed_entries = [_parse_entry(entry) for entry in entries]
    return parsed_entries


def _parse_entry(entry):
    return FeedEntry(
        entry["id"],
        entry["link"],
        entry["summary"],
        [FeedMedia(media["url"], media["type"]) for media in entry["media_content"]],
    )
