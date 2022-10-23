from time import strptime
from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.reader import get_latest_data

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"

ENTRIES = [
    FeedParserDict({"published_parsed": strptime("02.02.2002", "%d.%m.%Y")}),
    FeedParserDict({"published_parsed": strptime("01.01.2001", "%d.%m.%Y")}),
    FeedParserDict({"published_parsed": strptime("04.04.2004", "%d.%m.%Y")}),
    FeedParserDict({"published_parsed": strptime("03.03.2003", "%d.%m.%Y")}),
]
EXPECTED_LATEST_ID = "LATEST_ID"
EXPECTED_LATEST_LINK = "LATEST_LINK"
EXPECTED_LATEST_DATE = strptime("05.05.2005", "%d.%m.%Y")
EXPECTED_LATEST_ENTRY_DATA = (EXPECTED_LATEST_ID, EXPECTED_LATEST_LINK, EXPECTED_LATEST_DATE)
LATEST_ENTRY = FeedParserDict(
    {
        "id": EXPECTED_LATEST_ID,
        "link": EXPECTED_LATEST_LINK,
        "published_parsed": EXPECTED_LATEST_DATE,
    }
)


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: {"url": FEED_LINK}})
@mark.parametrize(
    argnames="entries",
    argvalues=[
        ENTRIES + [LATEST_ENTRY],
        [LATEST_ENTRY] + ENTRIES,
        ENTRIES[:2] + [LATEST_ENTRY] + ENTRIES[2:],
    ],
)
def test_get_latest_data(entries: list[FeedParserDict]) -> None:
    feed = FeedParserDict({"href": FEED_LINK, "entries": entries})
    assert EXPECTED_LATEST_ENTRY_DATA == get_latest_data(feed)
