from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.reader import feed_is_valid
from settings import Settings

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"


@patch.object(Settings, "RSS_FEEDS", {FEED_TYPE: {"url": FEED_LINK}})
@mark.parametrize(
    argnames=("parsed_rss", "expected_validity"),
    argvalues=[
        (
            FeedParserDict(
                {
                    "href": FEED_LINK,
                    "status": 200,
                    "entries": [FeedParserDict({"id": "ID", "link": "LINK"})],
                }
            ),
            True,
        ),
        (
            FeedParserDict(
                {
                    "href": FEED_LINK,
                    "status": 301,
                    "entries": [FeedParserDict({"id": "ID"})],
                }
            ),
            True,
        ),
        (FeedParserDict({"href": FEED_LINK, "status": 200, "entries": []}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 301, "entries": []}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 200}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 301}), False),
        (FeedParserDict({"href": FEED_LINK, "status": 200, "entries": [{}]}), False),
        (
            FeedParserDict(
                {
                    "href": FEED_LINK,
                    "status": 200,
                    "entries": [
                        {
                            "link": "LINK",
                            "published_parsed": (2000, 1, 1, 0, 0, 0, 0, 1, -1),
                        }
                    ],
                }
            ),
            True,
        ),
        (
            FeedParserDict(
                {"href": FEED_LINK, "status": 200, "entries": [{"link": "LINK"}]}
            ),
            True,
        ),
        (
            FeedParserDict(
                {
                    "href": FEED_LINK,
                    "status": 200,
                    "entries": [{"published_parsed": (2000, 1, 1, 0, 0, 0, 0, 1, -1)}],
                }
            ),
            True,
        ),
        (
            FeedParserDict(
                {
                    "href": FEED_LINK,
                    "status": 400,
                    "entries": [FeedParserDict({"id": "ID", "link": "LINK"})],
                }
            ),
            False,
        ),
    ],
)
def test_feed_is_valid(parsed_rss: FeedParserDict, expected_validity: bool) -> None:
    assert expected_validity == bool(feed_is_valid(parsed_rss))
