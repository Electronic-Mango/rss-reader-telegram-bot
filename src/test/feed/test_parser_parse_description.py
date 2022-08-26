from unittest.mock import patch

from feedparser import FeedParserDict

from feed.parser import parse_description

FEED_TYPE = "FEED_TYPE"
ENTRY = FeedParserDict({"summary": "\n\n\n<b>bold text</b><a>\n\nlink text</a> raw\ntext\n\n\n"})
EXPECTED_DESCRIPTION = "bold text\n\nlink text raw\ntext"
FILTERS = ["nk te", "w\nt"]
EXPECTED_FILTERED_DESCRIPTION = "bold text\n\nlixt raext"


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {"show_description": True}})
def test_parse_description_description_enabled() -> None:
    assert EXPECTED_DESCRIPTION == parse_description(ENTRY, FEED_TYPE)


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {"show_description": True, "filters": FILTERS}})
def test_parse_description_with_filtering() -> None:
    assert EXPECTED_FILTERED_DESCRIPTION == parse_description(ENTRY, FEED_TYPE)


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {}})
def test_parse_description_description_disabled() -> None:
    assert parse_description(ENTRY, FEED_TYPE) is None
