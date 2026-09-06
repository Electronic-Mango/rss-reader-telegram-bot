from unittest.mock import patch

from feedparser import FeedParserDict

from feed.parser import parse_title
from settings_new import Settings

FEED_TYPE = "FEED_TYPE"
ENTRY = FeedParserDict({"title": "\n\n\ntext\n\nmore\ntext\n\n\n"})
EXPECTED_TITLE = "<b>text\n\nmore\ntext</b>"
FILTERS = ["\n\nmore", "xt"]
EXPECTED_FILTERED_TITLE = "<b>te\nte</b>"


@patch.object(Settings, "RSS_FEEDS", {FEED_TYPE: {"show_title": True}})
def test_parse_title_enabled() -> None:
    assert parse_title(ENTRY, FEED_TYPE) == EXPECTED_TITLE


@patch.object(
    Settings, "RSS_FEEDS", {FEED_TYPE: {"show_title": True, "filters": FILTERS}}
)
def test_parse_title_filtered() -> None:
    assert parse_title(ENTRY, FEED_TYPE) == EXPECTED_FILTERED_TITLE


@patch.object(Settings, "RSS_FEEDS", {FEED_TYPE: {}})
def test_parse_title_disabled() -> None:
    assert parse_title(ENTRY, FEED_TYPE) is None
