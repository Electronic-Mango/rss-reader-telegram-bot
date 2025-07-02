from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.parser import parse_description

FEED_TYPE = "FEED_TYPE"
ENTRY = FeedParserDict({"summary": "\n\n\n<b>bold text</b><a>\n\nlink text</a> raw\ntext\n\n\n"})
EXPECTED_DESCRIPTION = "bold text\n\nlink text raw\ntext"
FILTERS = ["nk te", "w\nt"]
EXPECTED_FILTERED_DESCRIPTION = "bold text\n\nlixt raext"


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {"show_description": True}})
@mark.parametrize(
    ("summary", "expected_description"),
    [
        ("\n\n\n<b>bold text</b><a>\n\nlink text</a> raw\ntext\n\n\n", "bold text\n\nlink text raw\ntext"),
        ("<img title='A summary in title!'/>", "A summary in title!"),
        ("<a alt='A summary in alt!' title=' A summary in title!  '/>", "A summary in title!"),
        ("<a alt='  A summary in alt!  ' titl='A summary in titl!'/>", "A summary in alt!"),
        ("<img title='A summary in title!'/>  Summary in text!  ", "Summary in text!"),
        ("<a other_attr='some_value' />", None),
        ("", None),
    ],
)
def test_parse_description_description_enabled(summary, expected_description) -> None:
    entry = FeedParserDict({"summary": summary})
    assert expected_description == parse_description(entry, FEED_TYPE)


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {"show_description": True, "filters": FILTERS}})
def test_parse_description_with_filtering() -> None:
    assert EXPECTED_FILTERED_DESCRIPTION == parse_description(ENTRY, FEED_TYPE)


@patch("feed.parser.RSS_FEEDS", {FEED_TYPE: {}})
def test_parse_description_description_disabled() -> None:
    assert parse_description(ENTRY, FEED_TYPE) is None
