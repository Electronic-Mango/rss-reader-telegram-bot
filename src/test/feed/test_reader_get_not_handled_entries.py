from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark
from pytest_mock import MockerFixture

from feed.reader import get_not_handled_entries

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"

ENTRIES = [
    FeedParserDict({"published": "01.01.2001", "id": "ID-1"}),
    FeedParserDict({"published": "02.02.2002", "id": "ID-2"}),
    FeedParserDict({"published": "03.03.2003", "id": "ID-3"}),
    FeedParserDict({"published": "04.04.2004", "id": "ID-4"}),
    FeedParserDict({"published": "05.05.2005", "id": "ID-5"}),
]


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: FEED_LINK})
@mark.parametrize(
    argnames=["latest_id", "expected_entries"],
    argvalues=[
        ("ID-5", []),
        ("ID-0", ENTRIES),
        ("ID-3", ENTRIES[3:]),
    ],
)
def test_get_not_handled_entries(
    latest_id: str, expected_entries: list[FeedParserDict], mocker: MockerFixture
) -> None:
    mocker.patch("feed.reader.parse", return_value=FeedParserDict({"entries": ENTRIES}))
    assert expected_entries == get_not_handled_entries(FEED_TYPE, FEED_NAME, latest_id)
