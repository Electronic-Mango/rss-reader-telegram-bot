from unittest.mock import patch

from feedparser import FeedParserDict
from pytest import mark
from pytest_mock import MockerFixture

from feed.reader import get_latest_id

FEED_TYPE = "FEED_TYPE"
FEED_NAME = "FEED_NAME"
FEED_LINK = "FEED_LINK"

ENTRIES = [
    FeedParserDict({"published": "02.02.2002"}),
    FeedParserDict({"published": "01.01.2001"}),
    FeedParserDict({"published": "04.04.2004"}),
    FeedParserDict({"published": "03.03.2003"}),
]
EXPECTED_LATEST_ID = "LATEST_ID"
LATEST_ENTRY = FeedParserDict({"published": "05.05.2005", "id": EXPECTED_LATEST_ID})


@patch("feed.reader.RSS_FEEDS", {FEED_TYPE: FEED_LINK})
@mark.parametrize(
    argnames="entries",
    argvalues=[
        ENTRIES + [LATEST_ENTRY],
        [LATEST_ENTRY] + ENTRIES,
        ENTRIES[:2] + [LATEST_ENTRY] + ENTRIES[2:],
    ],
)
def test_get_latest_id(entries: list[FeedParserDict], mocker: MockerFixture) -> None:
    mocker.patch("feed.reader.parse", return_value=FeedParserDict({"entries": entries}))
    assert EXPECTED_LATEST_ID == get_latest_id(FEED_TYPE, FEED_NAME)
