from feedparser import FeedParserDict
from pytest import mark

from feed.reader import feed_is_valid

VALID_ENTRY = FeedParserDict({"id": "ID"})
INVALID_ENTRY = FeedParserDict({"link": "LINK"})


@mark.parametrize(
    argnames=("parsed_rss", "expected_validity"),
    argvalues=[
        (FeedParserDict({"status": 200, "entries": []}), False),
        (FeedParserDict({"status": 200, "entries": [{}]}), False),
        (FeedParserDict({"status": 301, "entries": []}), False),
        (FeedParserDict({"status": 200}), False),
        (FeedParserDict({"status": 301}), False),
        (FeedParserDict({"status": 400, "entries": [VALID_ENTRY]}), False),
        (FeedParserDict({"status": 200, "entries": [INVALID_ENTRY]}), False),
        (FeedParserDict({"status": 301, "entries": [INVALID_ENTRY]}), False),
        (FeedParserDict({"status": 200, "entries": [VALID_ENTRY]}), True),
        (FeedParserDict({"status": 301, "entries": [VALID_ENTRY]}), True),
    ],
)
def test_feed_is_valid(parsed_rss: FeedParserDict, expected_validity: bool) -> None:
    assert expected_validity == bool(feed_is_valid(parsed_rss))
