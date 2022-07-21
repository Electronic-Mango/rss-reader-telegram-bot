from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.reader import feed_is_valid

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: FEED_LINK})
@mark.parametrize(
    argnames=["parsed_rss", "expected_validity"],
    argvalues=[
        (FeedParserDict({"href": FEED_LINK, "status": 200, "entries": [None]}), True),
        (FeedParserDict({"href": FEED_LINK, "status": 301, "entries": [None]}), True),
        (FeedParserDict({"href": FEED_LINK, "status": 200, "entries": []}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 301, "entries": []}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 200}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 301}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 400, "entries": [None]}), False),
    ],
)
def test_feed_is_valid(parsed_rss: FeedParserDict, expected_validity: bool) -> None:
    assert expected_validity == bool(feed_is_valid(parsed_rss))
