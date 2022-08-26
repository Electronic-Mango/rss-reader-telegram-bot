from unittest.mock import patch

from feedparser import FeedParserDict

from feed.parser import parse_title

FEED_TYPE = "FEED_TYPE"
ENTRY = FeedParserDict({"title": "\n\n\ntext\n\nmore\ntext\n\n\n"})
EXPECTED_TITLE = "<b>text\n\nmore\ntext</b>"
FILTERS = ["\n\nmore", "xt"]
EXPECTED_FILTERED_TITLE = "<b>te\nte</b>"


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {"show_title": True}})
def test_parse_title_enabled() -> None:
    assert EXPECTED_TITLE == parse_title(ENTRY, FEED_TYPE)


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {"show_title": True, "filters": FILTERS}})
def test_parse_title_filtered() -> None:
    assert EXPECTED_FILTERED_TITLE == parse_title(ENTRY, FEED_TYPE)


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {}})
def test_parse_title_disabled() -> None:
    assert parse_title(ENTRY, FEED_TYPE) is None
