from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark
from pytest_mock import MockerFixture

from feed.reader import feed_is_valid

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: FEED_LINK})
@mark.parametrize(
    argnames=["parsed_rss", "expected_validity"],
    argvalues=[
        (FeedParserDict({"status": 200, "entries": [None]}), True),
        (FeedParserDict({"status": 301, "entries": [None]}), True),
        (FeedParserDict({"status": 200, "entries": []}), False),
        (FeedParserDict({"status": 301, "entries": []}), False),
        (FeedParserDict({"status": 200}), False),
        (FeedParserDict({"status": 301}), False),
        (FeedParserDict({"status": 400, "entries": [None]}), False),
    ],
)
def test_feed_is_valid(
    parsed_rss: FeedParserDict, expected_validity: bool, mocker: MockerFixture
) -> None:
    mocker.patch("feed.reader.parse", return_value=parsed_rss)
    assert expected_validity == bool(feed_is_valid(FEED_TYPE, FEED_NAME))
