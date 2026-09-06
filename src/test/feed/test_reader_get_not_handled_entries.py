from time import strptime, struct_time
from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.reader import get_not_handled_entries
from settings import Settings

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"
ENTRIES = [
    FeedParserDict({"published_parsed": strptime("01.01.01", "%d.%m.%y"), "id": "ID1"}),
    FeedParserDict({"published_parsed": strptime("02.02.02", "%d.%m.%y"), "id": "ID2"}),
    FeedParserDict({"published_parsed": strptime("03.03.03", "%d.%m.%y"), "id": "ID3"}),
    FeedParserDict({"published_parsed": strptime("04.04.04", "%d.%m.%y"), "id": "ID4"}),
    FeedParserDict({"published_parsed": strptime("05.05.05", "%d.%m.%y"), "id": "ID5"}),
]


@patch.object(Settings, "RSS_FEEDS", {FEED_TYPE: FEED_LINK})
@mark.parametrize(
    argnames=("entries", "latest_id", "latest_date", "expected_entries"),
    argvalues=[
        (ENTRIES, "ID5", strptime("05.05.2005", "%d.%m.%Y"), []),
        (ENTRIES, "ID0", strptime("01.01.2000", "%d.%m.%Y"), ENTRIES),
        (ENTRIES, "ID3", strptime("03.03.2003", "%d.%m.%Y"), ENTRIES[3:]),
        (ENTRIES, "ID2.5", strptime("03.02.2003", "%d.%m.%Y"), ENTRIES[2:]),
        (
            [
                FeedParserDict(
                    {
                        "link": "https://example.com/older",
                        "published_parsed": strptime("01.01.2001", "%d.%m.%Y"),
                    }
                ),
                FeedParserDict(
                    {
                        "link": "https://example.com/latest/",
                        "published_parsed": strptime("02.02.2002", "%d.%m.%Y"),
                    }
                ),
            ],
            "https://example.com/older",
            strptime("01.01.2001", "%d.%m.%Y"),
            [
                FeedParserDict(
                    {
                        "link": "https://example.com/latest/",
                        "published_parsed": strptime("02.02.2002", "%d.%m.%Y"),
                    }
                )
            ],
        ),
        (
            [FeedParserDict({"id": "NEW_ID"}), FeedParserDict({"id": "LATEST_ID"})],
            "LATEST_ID",
            None,
            [FeedParserDict({"id": "NEW_ID"})],
        ),
    ],
)
def test_get_not_handled_entries(
    entries: list[FeedParserDict],
    latest_id: str,
    latest_date: struct_time | None,
    expected_entries: list[FeedParserDict],
) -> None:
    feed = FeedParserDict({"href": FEED_LINK, "entries": entries})
    assert expected_entries == get_not_handled_entries(feed, latest_id, latest_date)
