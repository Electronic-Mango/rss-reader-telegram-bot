from time import strptime, struct_time
from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark

from feed.reader import get_not_handled_entries

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"
ENTRIES = [
    FeedParserDict({"published_parsed": strptime("01.01.2001", "%d.%m.%Y"), "id": "ID-1"}),
    FeedParserDict({"updated_parsed": strptime("02.02.2002", "%d.%m.%Y"), "id": "ID-2"}),
    FeedParserDict({"published_parsed": strptime("03.03.2003", "%d.%m.%Y"), "id": "ID-3"}),
    FeedParserDict({"updated_parsed": strptime("04.04.2004", "%d.%m.%Y"), "id": "ID-4"}),
    FeedParserDict({"published_parsed": strptime("05.05.2005", "%d.%m.%Y"), "id": "ID-5"}),
]


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: FEED_LINK})
@mark.parametrize(
    argnames=["latest_id", "latest_date", "expected_entries"],
    argvalues=[
        ("ID-5", strptime("05.05.2005", "%d.%m.%Y"), []),
        ("ID-0", strptime("01.01.2000", "%d.%m.%Y"), ENTRIES),
        ("ID-3", strptime("03.03.2003", "%d.%m.%Y"), ENTRIES[3:]),
        ("ID-2.5", strptime("04.03.2003", "%d.%m.%Y"), ENTRIES[2:]),
    ],
)
def test_get_not_handled_entries(
    latest_id: str, latest_date: struct_time, expected_entries: list[FeedParserDict]
) -> None:
    feed = FeedParserDict({"href": FEED_LINK, "entries": ENTRIES})
    assert expected_entries == get_not_handled_entries(feed, latest_id, latest_date)
