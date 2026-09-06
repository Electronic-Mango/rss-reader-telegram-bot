from time import strptime
from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.reader import get_latest_data
from settings import Settings

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
EXPECTED_LATEST_ENTRY_DATA = (
    EXPECTED_LATEST_ID,
    EXPECTED_LATEST_LINK,
    EXPECTED_LATEST_DATE,
)
LATEST_ENTRY = FeedParserDict(
    {
        "id": EXPECTED_LATEST_ID,
        "link": EXPECTED_LATEST_LINK,
        "published_parsed": EXPECTED_LATEST_DATE,
    }
)


@patch.object(Settings, "RSS_FEEDS", {FEED_TYPE: {"url": FEED_LINK}})
@mark.parametrize(
    argnames="entries",
    argvalues=[
        [*ENTRIES, LATEST_ENTRY],
        [LATEST_ENTRY, *ENTRIES],
        [*ENTRIES[:2], LATEST_ENTRY, *ENTRIES[2:]],
    ],
)
def test_get_latest_data(entries: list[FeedParserDict]) -> None:
    feed = FeedParserDict({"href": FEED_LINK, "entries": entries})
    assert get_latest_data(feed) == EXPECTED_LATEST_ENTRY_DATA


@patch.object(Settings, "RSS_FEEDS", {FEED_TYPE: {"url": FEED_LINK}})
@mark.parametrize(
    ("entries", "expected_data"),
    [
        (
            [
                FeedParserDict(
                    {
                        "title": "INVALID_ENTRY",
                        "published_parsed": strptime("06.06.2006", "%d.%m.%Y"),
                    }
                ),
                LATEST_ENTRY,
            ],
            EXPECTED_LATEST_ENTRY_DATA,
        ),
        (
            [FeedParserDict({"id": EXPECTED_LATEST_ID})],
            (EXPECTED_LATEST_ID, None, None),
        ),
        (
            [
                FeedParserDict(
                    {
                        "id": EXPECTED_LATEST_ID,
                        "published_parsed": EXPECTED_LATEST_DATE,
                    }
                )
            ],
            (EXPECTED_LATEST_ID, None, EXPECTED_LATEST_DATE),
        ),
        (
            [FeedParserDict({"link": EXPECTED_LATEST_LINK})],
            (None, EXPECTED_LATEST_LINK, None),
        ),
    ],
)
def test_get_latest_data_handles_missing_fields(entries, expected_data) -> None:
    feed = FeedParserDict({"href": FEED_LINK, "entries": entries})
    assert get_latest_data(feed) == expected_data
