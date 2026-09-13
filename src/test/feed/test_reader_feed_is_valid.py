from unittest.mock import patch

from pytest import mark

from feed.reader import feed_is_valid
from feed.types import RssFeed
from settings import Settings

FEED_TYPE = "FEED_TYPE"
VALID_ENTRY = {"id": "ID"}
INVALID_ENTRY = {"link": "LINK"}


@mark.parametrize(
    argnames=("parsed_rss", "expected_validity"),
    argvalues=[
        ({"status": 200, "entries": []}, False),
        ({"status": 200, "entries": [{}]}, False),
        ({"status": 301, "entries": []}, False),
        ({"status": 200}, False),
        ({"status": 301}, False),
        ({"status": 400, "entries": [VALID_ENTRY]}, False),
        ({"status": 200, "entries": [INVALID_ENTRY]}, False),
        ({"status": 301, "entries": [INVALID_ENTRY]}, False),
        ({"status": 200, "entries": [VALID_ENTRY]}, True),
        ({"status": 301, "entries": [VALID_ENTRY]}, True),
    ],
)
def test_feed_is_valid(parsed_rss: RssFeed, expected_validity: bool) -> None:
    assert expected_validity == bool(feed_is_valid(parsed_rss))


@patch.object(Settings, "RSS_FEEDS", {FEED_TYPE: {"entry_filters": {"title": "abc.*"}}})
@mark.parametrize(
    argnames=("title", "expected_valid"), argvalues=[("xyz", False), ("abcdef", True)]
)
def test_feed_is_valid_respects_entry_filters(title: str, expected_valid: bool) -> None:
    feed = {
        "status": 200,
        "feed_type": FEED_TYPE,
        "entries": [{"id": "ID", "title": title}],
    }
    assert feed_is_valid(feed) is expected_valid
