from unittest.mock import patch

from pytest import mark

from feed.reader import get_sorted_entries
from feed.types import RssEntry
from settings import Settings

FEED_TYPE = "FEED_TYPE"


@mark.parametrize(
    argnames=("entry_filters", "entry", "expected_included"),
    argvalues=[
        ({"title": "abc.*"}, {"id": "ID", "title": "abcdef"}, True),
        ({"title": "abc.*"}, {"id": "ID", "title": "xyz"}, False),
        ({"title": "abc.*"}, {"id": "ID"}, False),
        ({"title": "(?!.*bad)"}, {"id": "ID", "title": "good text"}, True),
        ({"title": "(?!.*bad)"}, {"id": "ID", "title": "this is bad text"}, False),
        ({"title": "(?!.*bad)"}, {"id": "ID"}, True),
        (
            {"title": "abc.*", "link": "(?!.*ignored)"},
            {"id": "ID", "title": "abcdef", "link": "http://example.com"},
            True,
        ),
        (
            {"title": "abc.*", "link": "(?!.*ignored)"},
            {"id": "ID", "title": "abcdef", "link": "http://ignored.com"},
            False,
        ),
    ],
)
def test_entry_filters(
    entry_filters: dict[str, str], entry: RssEntry, expected_included: bool
) -> None:
    feed = {"feed_type": FEED_TYPE, "entries": [entry]}
    rss_feeds = {FEED_TYPE: {"entry_filters": entry_filters}}
    with patch.object(Settings, "RSS_FEEDS", rss_feeds):
        result = get_sorted_entries(feed)
    assert (entry in result) == expected_included


@mark.parametrize(
    argnames=("rss_feeds", "feed"),
    argvalues=[
        (
            {FEED_TYPE: {}},
            {"feed_type": FEED_TYPE, "entries": [{"id": "ID", "title": "anything"}]},
        ),
        (
            {FEED_TYPE: {"entry_filters": {"title": "abc.*"}}},
            {"entries": [{"id": "ID", "title": "xyz"}]},
        ),
    ],
)
def test_entry_filters_bypassed(rss_feeds: dict[str, dict], feed: dict) -> None:
    entry = feed["entries"][0]
    with patch.object(Settings, "RSS_FEEDS", rss_feeds):
        assert get_sorted_entries(feed) == [entry]
